"""Testes do seam de recomendação.

Estratégia: os testes do fluxo NÃO baixam o BERT — injetam um encoder FAKE determinístico
(fixture `fake_encoder`) no lugar de `recomendacao._modelo`/`_centroide`. Há um único teste
`@pytest.mark.slow` (opt-in) que exercita o modelo real; ele pula sozinho se as deps de ML
(`uv sync --group embedding`) ou o asset do centróide não estiverem disponíveis.
"""

import hashlib
from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest

from app.core.config import get_settings
from app.models.politico import Politico
from app.services import recomendacao


class _FakeST:
    """Encoder fake: mapeia texto -> vetor 768d determinístico e normalizado (L2)."""

    def encode(self, textos, normalize_embeddings=True, convert_to_numpy=True):
        out = []
        for t in textos:
            seed = int.from_bytes(hashlib.sha256(t.encode("utf-8")).digest()[:4], "big")
            v = np.random.RandomState(seed).randn(768).astype("float32")
            if normalize_embeddings:
                v = v / np.linalg.norm(v)
            out.append(v)
        return np.asarray(out, dtype="float32")


@pytest.fixture
def fake_encoder(monkeypatch):
    """Substitui o modelo real por um encoder fake e o centróide por zeros."""
    monkeypatch.setattr(recomendacao, "_modelo", lambda: _FakeST())
    monkeypatch.setattr(recomendacao, "_centroide", lambda: np.zeros(768, dtype="float32"))
    yield


@pytest.fixture(autouse=True)
def _llm_desligado_por_padrao(monkeypatch):
    """Desliga o LLM (Groq) nos testes por padrão — sem rede; cai no texto-base.

    Esvazia a chave: justificativas_llm curto-circuita para {}. O teste unitário do LLM
    reativa a chave + injeta um cliente fake.
    """
    monkeypatch.setattr(recomendacao.settings, "groq_api_key", "")
    yield


# ----------------------------------------------------------------- gerar_embedding (unit)


def test_gerar_embedding_dim_e_norma(fake_encoder):
    v = recomendacao.gerar_embedding("saúde pública")
    assert len(v) == 768
    assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-5


def test_gerar_embedding_deterministico(fake_encoder):
    assert recomendacao.gerar_embedding("educação") == recomendacao.gerar_embedding("educação")


# ---------------------------------------------------------- evidências (unit)


def test_evidencias_seleciona_top_2_do_mesmo_politico(monkeypatch):
    query = np.zeros(768, dtype="float32")
    query[0] = 1.0
    vetores = np.zeros((4, 768), dtype="float32")
    vetores[:, 0] = [0.9, 0.86, 0.99, 0.2]
    registros = [
        recomendacao.PropostaEvidencia(
            nome="Ana",
            municipio="JP",
            tipo="REQ",
            numero=10,
            ano=2026,
            resumo="Solicita a reforma de uma unidade de saúde.",
        ),
        recomendacao.PropostaEvidencia(
            nome="Ana",
            municipio="JP",
            tipo="PL",
            numero=20,
            ano=2025,
            resumo="Cria um programa municipal de atendimento médico.",
        ),
        recomendacao.PropostaEvidencia(
            nome="Outra Pessoa",
            municipio="JP",
            tipo="REQ",
            numero=99,
            ano=2026,
            resumo="Esta proposta tem score maior, mas pertence a outro político.",
        ),
        recomendacao.PropostaEvidencia(
            nome="Ana",
            municipio="JP",
            tipo="REQ",
            numero=30,
            ano=2024,
            resumo="Solicita pintura de uma praça.",
        ),
    ]
    monkeypatch.setattr(recomendacao, "_centroide", lambda: np.zeros(768, dtype="float32"))
    monkeypatch.setattr(recomendacao, "_base_evidencias", lambda: (vetores, registros))
    politico = Politico(id=uuid4(), nome="Ana", municipio="JP")

    evidencias = recomendacao.evidencias_para_politico(query.tolist(), politico, limite=2)

    assert [e.numero for e in evidencias] == [10, 20]


def test_evidencias_omite_segunda_proposta_quando_afinidade_cai_demais(monkeypatch):
    query = np.zeros(768, dtype="float32")
    query[0] = 1.0
    vetores = np.zeros((2, 768), dtype="float32")
    vetores[:, 0] = [0.9, 0.3]
    registros = [
        recomendacao.PropostaEvidencia(
            nome="Ana",
            municipio="JP",
            tipo="REQ",
            numero=10,
            ano=2026,
            resumo="Solicita a reforma de uma unidade de saúde.",
        ),
        recomendacao.PropostaEvidencia(
            nome="Ana",
            municipio="JP",
            tipo="PL",
            numero=20,
            ano=2025,
            resumo="Renomeia uma rua sem relação com a pauta informada.",
        ),
    ]
    monkeypatch.setattr(recomendacao, "_centroide", lambda: np.zeros(768, dtype="float32"))
    monkeypatch.setattr(recomendacao, "_base_evidencias", lambda: (vetores, registros))
    politico = Politico(id=uuid4(), nome="Ana", municipio="JP")

    evidencias = recomendacao.evidencias_para_politico(query.tolist(), politico, limite=2)

    assert [e.numero for e in evidencias] == [10]


def test_evidencias_abaixo_do_piso_nao_viram_evidencia(monkeypatch):
    # nenhuma proposta do político é realmente sobre a query → lista vazia (não inventa)
    query = np.zeros(768, dtype="float32")
    query[0] = 1.0
    vetores = np.zeros((2, 768), dtype="float32")
    vetores[:, 0] = [0.10, 0.05]  # ambos abaixo de EVIDENCE_MIN_SCORE
    registros = [
        recomendacao.PropostaEvidencia(
            nome="Ana", municipio="JP", tipo="REQ", numero=10, ano=2026,
            resumo="Renomeia uma rua sem relação com a pauta informada.",
        ),
        recomendacao.PropostaEvidencia(
            nome="Ana", municipio="JP", tipo="REQ", numero=20, ano=2026,
            resumo="Concede título honorífico a um cidadão.",
        ),
    ]
    monkeypatch.setattr(recomendacao, "_base_evidencias", lambda: (vetores, registros))
    politico = Politico(id=uuid4(), nome="Ana", municipio="JP")

    assert recomendacao.evidencias_para_politico(query.tolist(), politico, limite=2) == []


def test_justificativa_cita_temas_das_evidencias():
    politico = Politico(id=uuid4(), nome="Ana Silva", municipio="JP")
    evidencias = [
        recomendacao.PropostaEvidencia(
            nome="Ana Silva", municipio="JP", tipo="REQ", numero=10, ano=2026,
            resumo="Propõe instalar postos de vacinação móveis próximos às escolas.",
        ),
    ]
    texto = recomendacao.justificativa_para(politico, evidencias)
    assert texto is not None
    assert texto.startswith("Ana")
    # cita ao menos um tema concreto extraído do resumo
    assert any(t in texto.lower() for t in ("vacinacao", "vacinação", "postos", "escolas"))
    assert recomendacao.justificativa_para(politico, []) is None


def test_justificativas_llm_mapeia_frase_por_politico(monkeypatch):
    """Com um cliente Groq fake, a frase JSON (por índice) volta mapeada por politico.id."""
    p1 = Politico(id=uuid4(), nome="Ana", municipio="JP")
    p2 = Politico(id=uuid4(), nome="Bia", municipio="JP")
    ev = [recomendacao.PropostaEvidencia(
        nome="Ana", municipio="JP", tipo="REQ", numero=1, ano=2026, resumo="ciclovias")]

    class _Msg:
        content = '{"0": "Ana criou ciclovias no centro.", "1": "Bia ampliou postos de saúde."}'

    class _FakeGroq:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(**kwargs):
                    return type("R", (), {"choices": [type("C", (), {"message": _Msg()})()]})()

    monkeypatch.setattr(recomendacao.settings, "groq_api_key", "x")  # passa o guard
    monkeypatch.setattr(recomendacao, "_groq_client", lambda: _FakeGroq())

    out = recomendacao.justificativas_llm("ciclovias e saúde", [(p1, ev), (p2, ev)])
    assert out[p1.id] == "Ana criou ciclovias no centro."
    assert out[p2.id] == "Bia ampliou postos de saúde."
    # sem chave → degrada para {} (sem rede)
    monkeypatch.setattr(recomendacao.settings, "groq_api_key", "")
    assert recomendacao.justificativas_llm("x", [(p1, ev)]) == {}


def test_evidencias_ausentes_nao_interrompem_ranking(monkeypatch):
    monkeypatch.setattr(
        recomendacao,
        "_base_evidencias",
        lambda: (np.empty((0, 768), dtype="float32"), []),
    )
    politico = Politico(id=uuid4(), nome="Ana", municipio="JP")

    assert recomendacao.evidencias_para_politico([0.0] * 768, politico) == []


# ------------------------------------------------------------------------- fluxo E2E


def test_recomendacao_placeholder_sem_interesses(client, auth_headers):
    resp = client.get("/recomendacoes", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["placeholder"] is True


def test_recomendacao_com_match(fake_encoder, client, auth_headers, db):
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
    assert (
        client.post(
            "/usuarios/me/interesses", headers=auth_headers, json={"texto": texto}
        ).status_code
        == 200
    )

    resp = client.get("/recomendacoes", headers=auth_headers)
    body = resp.json()
    assert body["placeholder"] is False
    assert len(body["top_politicos"]) == 1
    assert body["top_politicos"][0]["nome"] == "Vereadora Exemplo"
    assert body["top_politicos"][0]["score"] > 0.99  # vetores idênticos
    assert body["cluster_alinhado"] == 3


def test_recomendacao_ordena_por_afinidade(fake_encoder, client, auth_headers, db):
    """O político cujo perfil casa com a query deve vir à frente do desalinhado."""
    db.add_all(
        [
            Politico(
                nome="Pró-Saúde",
                municipio="JP",
                cluster_id=1,
                embedding=recomendacao.gerar_embedding("saude postos atendimento medico"),
            ),
            Politico(
                nome="Pró-Trânsito",
                municipio="JP",
                cluster_id=2,
                embedding=recomendacao.gerar_embedding("transito asfalto pavimentacao vias"),
            ),
        ]
    )
    db.commit()

    client.post(
        "/usuarios/me/interesses",
        headers=auth_headers,
        json={"texto": "saude postos atendimento medico"},
    )
    body = client.get("/recomendacoes", headers=auth_headers).json()
    assert body["placeholder"] is False
    assert body["top_politicos"][0]["nome"] == "Pró-Saúde"
    # o 1º (alinhado) tem score maior que o 2º (desalinhado)
    assert body["top_politicos"][0]["score"] > body["top_politicos"][1]["score"]
    assert body["cluster_alinhado"] == 1


def test_recomendacao_inclui_justificativa_e_duas_propostas_sem_links(
    fake_encoder, monkeypatch, client, auth_headers, db
):
    texto = "saude postos atendimento medico"
    vetor = np.asarray(recomendacao.gerar_embedding(texto), dtype="float32")
    politico = Politico(
        nome="Pró-Saúde",
        municipio="JP",
        cluster_id=1,
        embedding=vetor.astype(float).tolist(),
    )
    db.add(politico)
    db.commit()

    vetores = np.stack([vetor, vetor * 0.95, -vetor]).astype("float32")
    registros = [
        recomendacao.PropostaEvidencia(
            nome="Pró-Saúde",
            municipio="JP",
            tipo="REQ",
            numero=101,
            ano=2026,
            resumo="Solicita reforma e ampliação de um posto de saúde.",
        ),
        recomendacao.PropostaEvidencia(
            nome="Pró-Saúde",
            municipio="JP",
            tipo="PL",
            numero=12,
            ano=2025,
            resumo="Cria atendimento médico itinerante nos bairros.",
        ),
        recomendacao.PropostaEvidencia(
            nome="Pró-Saúde",
            municipio="JP",
            tipo="REQ",
            numero=77,
            ano=2024,
            resumo="Solicita melhorias em uma praça.",
        ),
    ]
    monkeypatch.setattr(recomendacao, "_centroide", lambda: np.zeros(768, dtype="float32"))
    monkeypatch.setattr(recomendacao, "_base_evidencias", lambda: (vetores, registros))

    resposta = client.post(
        "/recomendacoes",
        headers=auth_headers,
        json={"texto": texto},
    )

    assert resposta.status_code == 200
    match = resposta.json()["top_politicos"][0]
    # justificativa agora é ESPECÍFICA: cita o político e os temas reais (não genérica)
    assert match["justificativa"] is not None
    assert "Pró-Saúde" in match["justificativa"]
    assert "saúde" in match["justificativa"].lower() or "posto" in match["justificativa"].lower()
    # as 2 propostas mais próximas semanticamente; a praça (77, irrelevante) fica de fora
    assert {e["numero"] for e in match["evidencias"]} == {101, 12}
    assert all("url" not in evidencia for evidencia in match["evidencias"])
    assert client.get("/recomendacoes", headers=auth_headers).json()["placeholder"] is False


# ---------------------------------------------------------- BERT real (opt-in, lento)


@pytest.mark.slow
def test_gerar_embedding_bert_real_smoke():
    """Carrega o BERT real e o centróide; valida dim 768 e norma unitária.

    Pula sozinho se sentence-transformers (grupo 'embedding') ou o centroid.npy
    não estiverem disponíveis.
    """
    pytest.importorskip("sentence_transformers")
    centroid = Path(get_settings().centroid_path)
    if not centroid.exists():
        pytest.skip(f"centróide ausente em {centroid} — rode 'make recommendation-build'")

    # limpa o cache do encoder fake/real entre testes
    recomendacao._modelo.cache_clear()
    recomendacao._centroide.cache_clear()

    v = np.asarray(recomendacao.gerar_embedding("saúde pública e educação"), dtype="float64")
    assert v.shape == (768,)
    assert abs(float(np.linalg.norm(v)) - 1.0) < 1e-4
    assert np.isfinite(v).all()
