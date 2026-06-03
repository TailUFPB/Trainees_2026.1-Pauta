import uuid

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.main import app

settings = get_settings()

# Tabelas limpas entre testes (na ordem que respeita as FKs).
_TABELAS = [
    "eventos_outbox",
    "inscricoes",
    "seguidores_politico",
    "problemas",
    "politicos",
    "users",
]


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


@pytest.fixture
def auth_headers(user_id: uuid.UUID) -> dict:
    """JWT válido assinado com o mesmo segredo que o backend valida (caminho real)."""
    token = jwt.encode(
        {"sub": str(user_id), "email": "cidadao@teste.com", "aud": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
