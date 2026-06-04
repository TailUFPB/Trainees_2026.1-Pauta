import io
import uuid

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
    # Mesmo autor faz transição válida (aberto -> resolvido); resolvido_por
    # pode ser fornecido no body e tem precedência sobre o email do JWT.
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


_TRANSICOES_VALIDAS_AUTOR = {
    ("aberto", "cancelado"),
    ("aberto", "resolvido"),
    ("em_andamento", "resolvido"),
}


def _criar(client, auth_headers):
    return client.post(
        "/problemas",
        headers=auth_headers,
        files={"foto": ("p.jpg", _imagem_png(), "image/png")},
        data={"lat": "-7.115", "lng": "-34.861"},
    ).json()


def test_patch_status_nao_autor_retorna_403(client, auth_headers, fazer_token):
    pid = _criar(client, auth_headers)["id"]
    outro = fazer_token(str(uuid.uuid4()))
    resp = client.patch(
        f"/problemas/{pid}/status",
        headers={"Authorization": f"Bearer {outro}"},
        json={"status": "resolvido"},
    )
    assert resp.status_code == 403


def test_patch_status_sem_auth_retorna_401(client, auth_headers):
    pid = _criar(client, auth_headers)["id"]
    resp = client.patch(f"/problemas/{pid}/status", json={"status": "resolvido"})
    assert resp.status_code == 401


def test_patch_status_autor_aberto_para_resolvido(client, auth_headers, db):
    pid = _criar(client, auth_headers)["id"]
    resp = client.patch(
        f"/problemas/{pid}/status",
        headers=auth_headers,
        json={"status": "resolvido"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "resolvido"
    # resolvido_por é preenchido automaticamente com o email do JWT
    assert body["resolvido_por"] == "cidadao@teste.com"
    assert body["resolvido_em"] is not None


def test_patch_status_autor_aberto_para_cancelado(client, auth_headers):
    pid = _criar(client, auth_headers)["id"]
    resp = client.patch(
        f"/problemas/{pid}/status", headers=auth_headers, json={"status": "cancelado"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelado"


def test_patch_status_autor_em_andamento_para_resolvido(client, auth_headers, db):
    from sqlalchemy import update

    from app.models.problema import Problema

    pid = _criar(client, auth_headers)["id"]
    # Coloca em_andamento via DB direto (simula ação operacional fora do escopo)
    db.execute(update(Problema).where(Problema.id == pid).values(status="em_andamento"))
    db.commit()

    resp = client.patch(
        f"/problemas/{pid}/status", headers=auth_headers, json={"status": "resolvido"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolvido"


def test_patch_status_autor_transicao_invalida_retorna_422(client, auth_headers):
    pid = _criar(client, auth_headers)["id"]
    # aberto -> arquivado é proibido pro autor
    resp = client.patch(
        f"/problemas/{pid}/status", headers=auth_headers, json={"status": "arquivado"}
    )
    assert resp.status_code == 422

    # aberto -> em_andamento também é proibido pro autor (operacional)
    resp = client.patch(
        f"/problemas/{pid}/status",
        headers=auth_headers,
        json={"status": "em_andamento"},
    )
    assert resp.status_code == 422


def test_get_problemas_lista_oculta_autor_e_descricao(client, auth_headers):
    # Cria com descrição
    resp = client.post(
        "/problemas",
        headers=auth_headers,
        files={"foto": ("p.png", _imagem_png(), "image/png")},
        data={
            "lat": "-7.115",
            "lng": "-34.861",
            "descricao": "buraco fundo na Rua João Silva, 123",
        },
    )
    assert resp.status_code == 201

    # GET público (lista)
    resp = client.get("/problemas")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert "autor_id" not in body[0]
    assert "descricao" not in body[0]
    # Campos públicos seguem presentes
    assert body[0]["tipo_problema"] is not None
    assert body[0]["lat"] is not None


def test_get_problema_anonimo_oculta_autor_e_descricao(client, auth_headers):
    resp = client.post(
        "/problemas",
        headers=auth_headers,
        files={"foto": ("p.png", _imagem_png(), "image/png")},
        data={"lat": "-7.115", "lng": "-34.861", "descricao": "endereço sensível"},
    )
    pid = resp.json()["id"]

    # GET sem auth
    resp_pub = client.get(f"/problemas/{pid}")
    assert resp_pub.status_code == 200
    assert "autor_id" not in resp_pub.json()
    assert "descricao" not in resp_pub.json()


def test_get_problema_autor_recebe_campos_completos(client, auth_headers):
    # /problemas/{id} virou público puro na Fatia 1.5; autor obtém detalhe completo via /usuarios/me/problemas/{id}
    resp = client.post(
        "/problemas",
        headers=auth_headers,
        files={"foto": ("p.png", _imagem_png(), "image/png")},
        data={"lat": "-7.115", "lng": "-34.861", "descricao": "minha descrição"},
    )
    pid = resp.json()["id"]

    # GET com auth do autor
    resp_auth = client.get(f"/problemas/{pid}", headers=auth_headers)
    assert resp_auth.status_code == 200
    body = resp_auth.json()
    assert "autor_id" not in body
    assert "descricao" not in body


def test_get_problema_outro_usuario_oculta_autor_e_descricao(client, auth_headers, fazer_token):
    resp = client.post(
        "/problemas",
        headers=auth_headers,
        files={"foto": ("p.png", _imagem_png(), "image/png")},
        data={"lat": "-7.115", "lng": "-34.861", "descricao": "PII"},
    )
    pid = resp.json()["id"]

    outro_token = fazer_token(str(uuid.uuid4()))
    resp_outro = client.get(
        f"/problemas/{pid}", headers={"Authorization": f"Bearer {outro_token}"}
    )
    assert resp_outro.status_code == 200
    assert "autor_id" not in resp_outro.json()
    assert "descricao" not in resp_outro.json()
