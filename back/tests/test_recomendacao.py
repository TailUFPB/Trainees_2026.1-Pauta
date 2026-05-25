from app.models.politico import Politico
from app.services import recomendacao


def test_recomendacao_placeholder_sem_interesses(client, auth_headers):
    resp = client.get("/recomendacoes", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["placeholder"] is True


def test_recomendacao_com_match(client, auth_headers, db):
    # Político com embedding alinhado ao texto de interesse.
    texto = "saude publica e educacao"
    db.add(
        Politico(
            nome="Vereadora Exemplo",
            cargo="Vereadora",
            partido="XYZ",
            municipio="Cabedelo",
            cluster_id=3,
            embedding=recomendacao.gerar_embedding(texto),
        )
    )
    db.commit()

    # Usuário define os mesmos interesses → similaridade alta.
    assert client.post(
        "/usuarios/me/interesses", headers=auth_headers, json={"texto": texto}
    ).status_code == 200

    resp = client.get("/recomendacoes", headers=auth_headers)
    body = resp.json()
    assert body["placeholder"] is False
    assert len(body["top_politicos"]) == 1
    assert body["top_politicos"][0]["nome"] == "Vereadora Exemplo"
    assert body["top_politicos"][0]["score"] > 0.99  # vetores idênticos
    assert body["cluster_alinhado"] == 3
