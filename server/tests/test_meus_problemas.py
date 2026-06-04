"""GET /usuarios/me/problemas — lista apenas reportes do autor com filtros."""

import io
import uuid

from PIL import Image


def _foto_valida_bytes() -> bytes:
    img = Image.new("RGB", (800, 600), (200, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _criar_problema(client, auth_headers, **extras):
    return client.post(
        "/problemas",
        headers=auth_headers,
        files={"foto": ("p.jpg", _foto_valida_bytes(), "image/jpeg")},
        data={"lat": "-7.115", "lng": "-34.861", **extras},
    )


def test_lista_vazia_para_novo_usuario(client, auth_headers):
    resp = client.get("/usuarios/me/problemas", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_lista_apenas_do_autor(client, auth_headers, fazer_token):
    # autor 1 cria 2 reportes
    _criar_problema(client, auth_headers)
    _criar_problema(client, auth_headers)
    # autor 2 cria 1 reporte
    outro = fazer_token(str(uuid.uuid4()))
    _criar_problema(client, {"Authorization": f"Bearer {outro}"})

    resp = client.get("/usuarios/me/problemas", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    for p in body:
        assert "autor_id" not in p  # autor_id removido; autoria é via HMAC interno


def test_filtro_status(client, auth_headers, db):
    r1 = _criar_problema(client, auth_headers)
    pid = r1.json()["id"]
    # Marca como resolvido
    client.patch(
        f"/problemas/{pid}/status", headers=auth_headers, json={"status": "resolvido"}
    )
    _criar_problema(client, auth_headers)  # esse fica aberto

    resp = client.get("/usuarios/me/problemas?status=resolvido", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "resolvido"


def test_paginacao(client, auth_headers):
    for _ in range(3):
        _criar_problema(client, auth_headers)
    resp = client.get(
        "/usuarios/me/problemas?limite=2&offset=0", headers=auth_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    resp2 = client.get(
        "/usuarios/me/problemas?limite=2&offset=2", headers=auth_headers
    )
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1


def test_requer_autenticacao(client):
    resp = client.get("/usuarios/me/problemas")
    assert resp.status_code == 401
