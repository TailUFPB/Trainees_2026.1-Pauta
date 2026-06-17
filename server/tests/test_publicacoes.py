"""POST /publicacoes (multipart, foto opcional) + GET /usuarios/me/publicacoes."""

import io

from PIL import Image

from app.services import storage


def _imagem_png(tamanho: int = 300) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (tamanho, tamanho), (90, 140, 90)).save(buf, format="PNG")
    return buf.getvalue()


def test_criar_publicacao_publica(client, auth_headers) -> None:
    resp = client.post(
        "/publicacoes",
        data={"conteudo": "Olá feed!", "anonimo": "false"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["conteudo"] == "Olá feed!"
    assert body["anonimo"] is False
    assert body["autor_nome"] is not None
    assert body["imagem_url"] is None


def test_criar_publicacao_anonima(client, auth_headers) -> None:
    resp = client.post(
        "/publicacoes",
        data={"conteudo": "Anônimo aqui.", "anonimo": "true"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["anonimo"] is True
    assert body["autor_nome"] is None


def test_criar_publicacao_com_foto(client, auth_headers, monkeypatch) -> None:
    """Com foto válida: valida a imagem e grava a URL devolvida pelo storage."""
    monkeypatch.setattr(storage, "salvar_foto", lambda conteudo, ct: "https://cdn.test/foto.png")
    resp = client.post(
        "/publicacoes",
        data={"conteudo": "Olha essa rua!", "anonimo": "false"},
        files={"foto": ("rua.png", _imagem_png(), "image/png")},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["imagem_url"] == "https://cdn.test/foto.png"


def test_criar_publicacao_foto_invalida_eh_422(client, auth_headers) -> None:
    """Arquivo que não é imagem válida é rejeitado antes de chegar ao storage."""
    resp = client.post(
        "/publicacoes",
        data={"conteudo": "x", "anonimo": "false"},
        files={"foto": ("nao.png", b"isso nao e uma imagem", "image/png")},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_criar_publicacao_sem_token_eh_401(client) -> None:
    resp = client.post("/publicacoes", data={"conteudo": "x", "anonimo": "false"})
    assert resp.status_code == 401


def test_criar_publicacao_conteudo_vazio_eh_422(client, auth_headers) -> None:
    resp = client.post(
        "/publicacoes",
        data={"conteudo": "", "anonimo": "false"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_criar_publicacao_whitespace_eh_422(client, auth_headers) -> None:
    resp = client.post(
        "/publicacoes",
        data={"conteudo": "   ", "anonimo": "false"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_listar_minhas_publicacoes_exclui_anonimas(client, auth_headers) -> None:
    """Anônimas NÃO aparecem em /usuarios/me/publicacoes porque autor_lookup é NULL."""
    client.post("/publicacoes", data={"conteudo": "a", "anonimo": "false"}, headers=auth_headers)
    client.post("/publicacoes", data={"conteudo": "b", "anonimo": "true"}, headers=auth_headers)
    resp = client.get("/usuarios/me/publicacoes", headers=auth_headers)
    assert resp.status_code == 200
    conteudos = [p["conteudo"] for p in resp.json()]
    assert "a" in conteudos
    assert "b" not in conteudos
