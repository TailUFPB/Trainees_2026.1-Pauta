"""GET /feed — timeline social unificada."""
import io

from PIL import Image


def _imagem_png() -> bytes:
    """Mesma helper de test_publicacoes/test_problemas — gera PNG válido pequeno.

    Usa 300x300 para passar o mínimo de 256px no menor lado.
    """
    img = Image.new("RGB", (300, 300), color=(120, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_feed_publico_sem_auth(client) -> None:
    # Leitura do feed é pública (visitante deslogado pode ver a timeline).
    assert client.get("/feed").status_code == 200


def test_feed_publico_mostra_itens_de_terceiros(client, auth_headers) -> None:
    # Um usuário autenticado publica; um visitante deslogado consegue ler.
    client.post(
        "/publicacoes",
        json={"conteudo": "visivel pra todos", "anonimo": False},
        headers=auth_headers,
    )
    resp = client.get("/feed?limite=10")  # sem headers
    assert resp.status_code == 200
    conteudos = [i.get("conteudo") for i in resp.json() if i["tipo"] == "publicacao"]
    assert "visivel pra todos" in conteudos


def test_feed_mistura_pub_e_problema_ordem_desc(client, auth_headers) -> None:
    client.post(
        "/publicacoes",
        json={"conteudo": "post1", "anonimo": False},
        headers=auth_headers,
    )
    client.post(
        "/problemas",
        data={"lat": -7.1, "lng": -34.9, "anonimo": "false"},
        files={"foto": ("x.png", _imagem_png(), "image/png")},
        headers=auth_headers,
    )
    client.post(
        "/publicacoes",
        json={"conteudo": "post2", "anonimo": False},
        headers=auth_headers,
    )

    resp = client.get("/feed?limite=10", headers=auth_headers)
    assert resp.status_code == 200
    itens = resp.json()
    assert len(itens) == 3
    tipos = [i["tipo"] for i in itens]
    assert "publicacao" in tipos and "problema" in tipos
    times = [i["created_at"] for i in itens]
    assert times == sorted(times, reverse=True)


def test_feed_anonima_sem_autor_nome(client, auth_headers) -> None:
    client.post(
        "/publicacoes",
        json={"conteudo": "anon", "anonimo": True},
        headers=auth_headers,
    )
    resp = client.get("/feed", headers=auth_headers)
    itens = resp.json()
    anon = next(i for i in itens if i["tipo"] == "publicacao" and i["conteudo"] == "anon")
    assert anon["anonimo"] is True
    assert anon["autor_nome"] is None
