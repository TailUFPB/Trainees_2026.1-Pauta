from types import SimpleNamespace

from app.services import visao


def test_visao_extrai_json_em_markdown() -> None:
    dados = visao._limpar_json(
        """```json
        {"tipo_problema": "asfalto", "severidade": "alta", "descricao": "Buraco grande.", "confianca": 0.82}
        ```"""
    )

    classificacao = visao._montar_classificacao(dados, "@cf/google/gemma-4-26b-a4b-it")

    assert classificacao.tipo_problema == "asfalto"
    assert classificacao.severidade == "alta"
    assert classificacao.resumo_llm == "Buraco grande."
    assert classificacao.confianca == 0.82


def test_visao_normaliza_resposta_invalida() -> None:
    classificacao = visao._montar_classificacao(
        {
            "problema_detectado": True,
            "tipo_problema": "valor_invalido",
            "severidade": "urgente",
            "descricao": "",
            "confianca": 87,
            "elementos_detectados": ["poste", "fio exposto"],
        },
        "modelo-teste",
    )

    assert classificacao.tipo_problema == "outros"
    assert classificacao.severidade == "baixa"
    assert classificacao.confianca == 0.87
    assert "poste" in classificacao.palavras_chave


def test_visao_fallback_sem_credenciais(monkeypatch) -> None:
    monkeypatch.setattr(
        visao,
        "get_settings",
        lambda: SimpleNamespace(
            cloudflare_account_id="",
            cloudflare_api_token="",
            cloudflare_ai_model="@cf/google/gemma-4-26b-a4b-it",
        ),
    )

    classificacao = visao.classificar(b"imagem")

    assert classificacao.tipo_problema == "outros"
    assert classificacao.severidade == "baixa"
    assert classificacao.confianca == 0.0
    assert classificacao.modelo_utilizado.endswith(":fallback")
