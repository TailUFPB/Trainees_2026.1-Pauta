import io

from PIL import Image
from sqlalchemy import select

from app.models.evento import EventoOutbox


def _imagem_png(tamanho: int = 300) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (tamanho, tamanho), (120, 120, 120)).save(buf, format="PNG")
    return buf.getvalue()


def _enviar_problema(client, headers, lat=-7.12, lng=-34.88):
    return client.post(
        "/problemas",
        headers=headers,
        files={"foto": ("foto.png", _imagem_png(), "image/png")},
        data={"lat": str(lat), "lng": str(lng), "descricao": "buraco na rua"},
    )


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_criar_problema_exige_auth(client):
    resp = _enviar_problema(client, headers={})
    assert resp.status_code == 401  # sem credenciais Bearer


def test_token_invalido(client):
    resp = client.get("/usuarios/me", headers={"Authorization": "Bearer xxx"})
    assert resp.status_code == 401


def test_fluxo_criar_problema(client, auth_headers, db):
    resp = _enviar_problema(client, auth_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert body["tipo_problema"] is not None
    assert body["severidade"] is not None
    assert body["foto_url"]
    assert body["lat"] == -7.12 and body["lng"] == -34.88
    # precisa_revisao deve ser coerente com a confiança.
    assert body["precisa_revisao"] == (body["confianca"] < 0.6)

    # Um evento problema.criado foi produzido no outbox.
    eventos = db.scalars(select(EventoOutbox)).all()
    assert len(eventos) == 1
    assert eventos[0].tipo == "problema.criado"
    assert eventos[0].payload["problema_id"] == body["id"]


def test_listar_por_bbox(client, auth_headers):
    _enviar_problema(client, auth_headers, lat=-7.12, lng=-34.88)

    # bbox cobrindo João Pessoa — encontra.
    dentro = client.get("/problemas", params={"bbox": "-35.0,-7.2,-34.8,-7.0"})
    assert dentro.status_code == 200
    assert len(dentro.json()) == 1

    # bbox em outra região — não encontra.
    fora = client.get("/problemas", params={"bbox": "-44.0,-23.0,-43.0,-22.0"})
    assert fora.json() == []


def test_imagem_pequena_rejeitada(client, auth_headers):
    buf = io.BytesIO()
    Image.new("RGB", (50, 50), (0, 0, 0)).save(buf, format="PNG")
    resp = client.post(
        "/problemas",
        headers=auth_headers,
        files={"foto": ("p.png", buf.getvalue(), "image/png")},
        data={"lat": "-7.1", "lng": "-34.8"},
    )
    assert resp.status_code == 422


def test_upload_excede_limite_rejeitado_com_413(client, auth_headers, monkeypatch):
    """Limite de upload é respeitado via leitura em chunks; deve abortar com 413."""
    from app.routers import problemas as router_problemas

    monkeypatch.setattr(router_problemas.settings, "max_upload_bytes", 1024)
    buf = io.BytesIO()
    Image.new("RGB", (1024, 1024), (200, 100, 50)).save(buf, format="JPEG", quality=85)
    payload = buf.getvalue()
    assert len(payload) > 1024  # garante que excede o limite

    resp = client.post(
        "/problemas",
        headers=auth_headers,
        files={"foto": ("grande.jpg", payload, "image/jpeg")},
        data={"lat": "-7.12", "lng": "-34.88", "descricao": "x"},
    )
    assert resp.status_code == 413, resp.text
    assert "maior" in resp.json()["detail"].lower()


def test_imagem_valida_passa_apos_verify(client, auth_headers):
    """Regressão: img.size é lido após reabrir o BytesIO (PIL exige isso pós-verify)."""
    resp = _enviar_problema(client, auth_headers)
    assert resp.status_code == 201, resp.text


def test_atualizar_status_emite_evento(client, auth_headers, db):
    pid = _enviar_problema(client, auth_headers).json()["id"]

    resp = client.patch(
        f"/problemas/{pid}/status",
        headers=auth_headers,
        json={"status": "resolvido", "resolvido_por": "ONG Cidade Limpa"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolvido"
    assert resp.json()["resolvido_por"] == "ONG Cidade Limpa"

    tipos = [e.tipo for e in db.scalars(select(EventoOutbox)).all()]
    assert "problema.status_alterado" in tipos
