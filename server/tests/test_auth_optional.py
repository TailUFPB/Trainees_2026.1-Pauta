"""get_current_user_optional retorna None sem 401 quando não há token."""


from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user_optional
from app.models.user import User


def _make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/me-or-anon")
    def route(user: User | None = Depends(get_current_user_optional)):
        return {"autenticado": user is not None}

    return app


def test_sem_token_retorna_none(client: TestClient = None):
    app = _make_app()
    c = TestClient(app)
    resp = c.get("/me-or-anon")
    assert resp.status_code == 200
    assert resp.json() == {"autenticado": False}


def test_com_token_valido_retorna_user(auth_headers: dict):
    app = _make_app()
    c = TestClient(app)
    resp = c.get("/me-or-anon", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"autenticado": True}


def test_com_token_invalido_retorna_none():
    app = _make_app()
    c = TestClient(app)
    resp = c.get("/me-or-anon", headers={"Authorization": "Bearer lixo"})
    # Decisão: token explicitamente inválido também retorna None silenciosamente,
    # porque o endpoint que usa get_current_user_optional não deve quebrar com
    # um header malformado vindo de um cliente público.
    assert resp.status_code == 200
    assert resp.json() == {"autenticado": False}
