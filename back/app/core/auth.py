"""Autenticação: valida o JWT emitido pelo Supabase Auth e resolve o usuário atual.

O Supabase assina os access tokens com HS256 usando o JWT secret do projeto
(Project Settings > API > JWT Secret). Validamos a assinatura e o audience, e fazemos
upsert do usuário na tabela local `users` (id = `sub` do token) na primeira visita.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User

settings = get_settings()
_bearer = HTTPBearer(auto_error=True)


def _decodificar(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    credenciais: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    claims = _decodificar(credenciais.credentials)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sem 'sub'")

    user_id = UUID(sub)
    user = db.get(User, user_id)
    if user is None:
        # Primeiro acesso: cria o registro local espelhando o auth.users do Supabase.
        user = User(id=user_id, email=claims.get("email"))
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
