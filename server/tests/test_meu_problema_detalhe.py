"""GET /usuarios/me/problemas/{id} — só autor recebe; 404 pra terceiros."""

import io
import uuid

from PIL import Image


def _foto() -> bytes:
    img = Image.new("RGB", (800, 600), (200, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _criar(client, headers):
    return client.post(
        "/problemas",
        headers=headers,
        files={"foto": ("p.jpg", _foto(), "image/jpeg")},
        data={"lat": "-7.115", "lng": "-34.861", "descricao": "minha descrição"},
    ).json()


def test_autor_recebe_detalhe_completo(client, auth_headers):
    pid = _criar(client, auth_headers)["id"]
    resp = client.get(f"/usuarios/me/problemas/{pid}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == pid
    assert body["descricao"] == "minha descrição"


def test_nao_autor_recebe_404(client, auth_headers):
    from jose import jwt

    from app.core.config import get_settings

    pid = _criar(client, auth_headers)["id"]
    outro = jwt.encode(
        {"sub": str(uuid.uuid4()), "email": "x@y.z", "aud": "authenticated"},
        get_settings().supabase_jwt_secret,
        algorithm="HS256",
    )
    resp = client.get(
        f"/usuarios/me/problemas/{pid}", headers={"Authorization": f"Bearer {outro}"}
    )
    assert resp.status_code == 404


def test_sem_auth_retorna_401(client, auth_headers):
    pid = _criar(client, auth_headers)["id"]
    resp = client.get(f"/usuarios/me/problemas/{pid}")
    assert resp.status_code == 401


def test_id_inexistente_retorna_404(client, auth_headers):
    fake = uuid.uuid4()
    resp = client.get(f"/usuarios/me/problemas/{fake}", headers=auth_headers)
    assert resp.status_code == 404
