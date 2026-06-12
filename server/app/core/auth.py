"""Autenticação: valida o JWT emitido pelo Supabase Auth (ES256 via JWKS) e resolve o usuário atual.

O Supabase assina os access tokens com ES256 usando chave assimétrica publicada no JWKS
do projeto (`/auth/v1/.well-known/jwks.json`). Validamos a assinatura e o audience, e fazemos
upsert do usuário na tabela local `users` (id = `sub` do token) na primeira visita.
"""

from typing import Any
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User

settings = get_settings()
bearer = HTTPBearer(auto_error=True)
_bearer_optional = HTTPBearer(auto_error=False)

# Cache do JWKS indexado por `kid`. Lazy: primeira request popula via HTTP.
# Em testes, conftest injeta a chave pública local antes que qualquer fetch aconteça.
_jwks_cache: dict[str, dict[str, Any]] = {}


def _fetch_jwks() -> None:
    """Busca o JWKS do Supabase e popula o cache módulo-level."""
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    resp = httpx.get(url, timeout=5.0)
    resp.raise_for_status()
    for key in resp.json().get("keys", []):
        kid = key.get("kid")
        if kid:
            _jwks_cache[kid] = key


def _signing_key(kid: str) -> dict[str, Any]:
    if kid not in _jwks_cache:
        _fetch_jwks()
    if kid not in _jwks_cache:
        raise JWTError(f"kid {kid!r} não encontrado no JWKS")
    return _jwks_cache[kid]


def _decodificar(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise JWTError("token sem 'kid' no header")
        return jwt.decode(
            token,
            _signing_key(kid),
            algorithms=["ES256"],
            audience="authenticated",
        )
    except (JWTError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _nome_publico_de_email(email: str | None) -> str | None:
    """Deriva nome_publico da parte local do email. None se email vazio/inválido."""
    if not email or "@" not in email:
        return None
    return email.split("@", 1)[0] or None


def get_current_user(
    credenciais: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    claims = _decodificar(credenciais.credentials)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem 'sub'")

    user_id = UUID(sub)
    email = claims.get("email")
    user = db.get(User, user_id)
    if user is None:
        # Primeiro acesso: cria o registro local espelhando o auth.users do Supabase.
        # nome_publico default = parte local do e-mail (usuário pode personalizar depois).
        user = User(id=user_id, nome_publico=_nome_publico_de_email(email))
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            # Requests concorrentes ou callbacks repetidos podem tentar inserir o mesmo
            # usuário ao mesmo tempo. Se já existir, reaproveita o registro persistido.
            db.rollback()
            user = db.get(User, user_id)
            if user is None:
                raise
    elif user.nome_publico is None:
        # Backfill lazy: usuários criados antes do nome_publico existir ganham um
        # default na primeira autenticação após esta mudança.
        novo_nome = _nome_publico_de_email(email)
        if novo_nome:
            user.nome_publico = novo_nome
            db.commit()
            db.refresh(user)
    return user


def get_current_user_optional(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    db: Session = Depends(get_db),
) -> User | None:
    """Variante de get_current_user que retorna None silenciosamente quando
    não há token ou ele é inválido — útil em endpoints que mudam de comportamento
    baseado em autenticação sem rejeitar o cliente público."""
    if credenciais is None:
        return None
    try:
        claims = _decodificar(credenciais.credentials)
    except HTTPException:
        return None
    sub = claims.get("sub")
    if not sub:
        return None
    user_id = UUID(sub)
    email = claims.get("email")
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, nome_publico=_nome_publico_de_email(email))
        db.add(user)
        db.commit()
        db.refresh(user)
    elif user.nome_publico is None:
        novo_nome = _nome_publico_de_email(email)
        if novo_nome:
            user.nome_publico = novo_nome
            db.commit()
            db.refresh(user)
    return user
