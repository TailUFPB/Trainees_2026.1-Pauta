import base64
import uuid
from collections.abc import Callable
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import text

from app.core import auth as auth_module
from app.db.session import SessionLocal, engine
from app.main import app

# Par ES256 gerado uma vez por processo de teste — evita custo a cada teste
# e mantém o mesmo `kid` consistente entre tokens emitidos.
_PRIV_KEY = ec.generate_private_key(ec.SECP256R1())
_PRIV_PEM = _PRIV_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()

_PUB_NUMBERS = _PRIV_KEY.public_key().public_numbers()
_TEST_KID = "test-kid"


def _b64url(n: int, length: int) -> str:
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()


_PUB_JWK: dict[str, Any] = {
    "kty": "EC",
    "crv": "P-256",
    "alg": "ES256",
    "use": "sig",
    "kid": _TEST_KID,
    "x": _b64url(_PUB_NUMBERS.x, 32),
    "y": _b64url(_PUB_NUMBERS.y, 32),
}

_TABELAS = [
    "notificacoes",
    "eventos_outbox",
    "inscricoes",
    "seguidores_politico",
    "publicacoes",
    "problemas",
    "politicos",
    "users",
]


@pytest.fixture(scope="session", autouse=True)
def _instalar_pgcrypto():
    """Garante pgcrypto no DB de teste — usado por cripto_autor (pgp_sym_encrypt).

    Idempotente; Task 3 da Fatia 2 instala via Alembic 0011, mas Task 2 roda
    antes e precisa da extensão já disponível pros testes."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    yield


@pytest.fixture(autouse=True)
def _mock_jwks():
    """Injeta a chave pública de teste no cache JWKS do auth — evita rede em testes."""
    auth_module._jwks_cache.clear()
    auth_module._jwks_cache[_TEST_KID] = _PUB_JWK
    yield
    auth_module._jwks_cache.clear()


@pytest.fixture(autouse=True)
def _limpar_banco():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE " + ", ".join(_TABELAS) + " RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


def _emitir_token(sub: str) -> str:
    return jwt.encode(
        {"sub": sub, "email": "cidadao@teste.com", "aud": "authenticated"},
        _PRIV_PEM,
        algorithm="ES256",
        headers={"kid": _TEST_KID},
    )


@pytest.fixture
def auth_headers(user_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {_emitir_token(str(user_id))}"}


@pytest.fixture
def fazer_token() -> Callable[[str], str]:
    """Emite um token ES256 válido para um `sub` arbitrário — usado por testes
    que precisam simular um segundo usuário (ex: dono X não-dono)."""
    return _emitir_token


@pytest.fixture
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
