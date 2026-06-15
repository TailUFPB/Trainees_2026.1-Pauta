"""POST /publicacoes + GET /usuarios/me/publicacoes."""


def test_criar_publicacao_publica(client, auth_headers) -> None:
    resp = client.post(
        "/publicacoes",
        json={"conteudo": "Olá feed!", "anonimo": False},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["conteudo"] == "Olá feed!"
    assert body["anonimo"] is False
    assert body["autor_nome"] is not None


def test_criar_publicacao_anonima(client, auth_headers) -> None:
    resp = client.post(
        "/publicacoes",
        json={"conteudo": "Anônimo aqui.", "anonimo": True},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["anonimo"] is True
    assert body["autor_nome"] is None


def test_criar_publicacao_sem_token_eh_401(client) -> None:
    resp = client.post("/publicacoes", json={"conteudo": "x", "anonimo": False})
    assert resp.status_code == 401


def test_criar_publicacao_conteudo_vazio_eh_422(client, auth_headers) -> None:
    resp = client.post(
        "/publicacoes",
        json={"conteudo": "", "anonimo": False},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_criar_publicacao_whitespace_eh_422(client, auth_headers) -> None:
    resp = client.post(
        "/publicacoes",
        json={"conteudo": "   ", "anonimo": False},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_listar_minhas_publicacoes_exclui_anonimas(client, auth_headers) -> None:
    """Anônimas NÃO aparecem em /usuarios/me/publicacoes porque autor_lookup é NULL."""
    client.post("/publicacoes", json={"conteudo": "a", "anonimo": False}, headers=auth_headers)
    client.post("/publicacoes", json={"conteudo": "b", "anonimo": True}, headers=auth_headers)
    resp = client.get("/usuarios/me/publicacoes", headers=auth_headers)
    assert resp.status_code == 200
    conteudos = [p["conteudo"] for p in resp.json()]
    assert "a" in conteudos
    assert "b" not in conteudos
