"""Seam do sistema de recomendação (lado backend).

Liga o app ao pipeline offline (recommendation/) por DUAS funções:

1. `gerar_embedding(texto)` — projeta o texto de pautas do cidadão no MESMO espaço 768d
   em que os perfis dos políticos foram gerados: BERT português (normalizado L2) →
   subtrai o centróide do corpus → re-normaliza L2. É o espelho de
   `recommendation/src/embeddings.projetar_no_espaco`; um teste de paridade garante que
   os dois caminhos produzem o mesmo vetor (cosine > 0.99). Modelo e centróide são
   carregados uma única vez (lru_cache) e aquecidos no startup (ver main.lifespan).
2. `top_politicos_por_similaridade(db, vetor, limite)` — busca de cosseno no pgvector
   (`<=>`, índice HNSW). Roda dentro do Postgres; só depende dos embeddings dos políticos
   estarem populados (ver app/cli/seed_vetores.py).

As dependências de ML (sentence-transformers/torch) são um GRUPO OPCIONAL do pyproject
(`embedding`): só necessárias para gerar embeddings de query em produção. Os testes
injetam um encoder fake (sem baixar BERT).
"""

import csv
import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.politico import Politico

settings = get_settings()
logger = logging.getLogger(__name__)
# Evidências: similaridade semântica (cosseno no espaço centrado do SBERT).
EVIDENCE_MIN_SCORE = 0.25  # piso: abaixo disso a proposta não é "sobre" a query → não vira evidência
MAX_EVIDENCE_SCORE_GAP = 0.08  # mostra a 2ª proposta só se quase tão próxima quanto a 1ª
# Temas municipais conhecidos (normalizados, sem acento). A justificativa cita SÓ termos
# desta whitelist encontrados nos resumos — evita vazar verbos/boilerplate ("pede", "propõe",
# "criação"). Se nenhum tema casar, usa um texto-base honesto. É só copy de UI; o casamento
# em si é 100% semântico (SBERT).
_TEMAS_STR = (
    "saude vacinacao vacina vacinas hospital hospitais posto postos clinica clinicas medico "
    "medica medicos ambulancia creche creches educacao escola escolas merenda ensino professor "
    "professores alfabetizacao transporte mobilidade ciclovia ciclovias onibus motorista "
    "motoristas transito pavimentacao asfalto calcada calcadas viaduto estacionamento seguranca "
    "iluminacao policiamento policia guarda camera cameras ambiente ambiental arborizacao arvore "
    "arvores reciclagem lixo residuos saneamento agua esgoto drenagem enchente limpeza cultura "
    "cultural esporte esportes lazer turismo moradia habitacao emprego trabalho renda assistencia "
    "mulher mulheres idoso idosos crianca criancas juventude deficiencia acessibilidade animal "
    "animais veterinario alimentacao feira agricultura praca parque"
)
TEMAS_CONHECIDOS = set(_TEMAS_STR.split())


@dataclass(frozen=True)
class PropostaEvidencia:
    """Proposta real que sustenta uma recomendação."""

    nome: str
    municipio: str
    tipo: str | None
    numero: int | None
    ano: int | None
    resumo: str


@lru_cache(maxsize=1)
def _modelo():
    """Carrega o modelo de embedding uma única vez (dep opcional: import tardio)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model_name)


@lru_cache(maxsize=1)
def _centroide() -> np.ndarray:
    """Carrega o centróide do corpus (asset exportado de recommendation/models/)."""
    caminho = Path(settings.centroid_path)
    if not caminho.exists():
        raise FileNotFoundError(
            f"Centróide não encontrado em '{caminho}'. Exporte recommendation/models/"
            "centroid.npy para o backend (Makefile: server-seed-vetores) ou ajuste "
            "CENTROID_PATH."
        )
    return np.load(caminho).astype(np.float32)


def _inteiro_ou_none(valor: str | None) -> int | None:
    if valor is None or not valor.strip():
        return None
    return int(float(valor))


@lru_cache(maxsize=1)
def _base_evidencias() -> tuple[np.ndarray, list[PropostaEvidencia]]:
    """Carrega embeddings e metadados das propostas; falha de forma degradável."""
    embeddings_path = Path(settings.proposal_embeddings_path)
    meta_path = Path(settings.proposal_embeddings_meta_path)
    if not embeddings_path.is_file() or not meta_path.is_file():
        return np.empty((0, settings.embedding_dim), dtype=np.float32), []

    try:
        vetores = np.load(embeddings_path).astype(np.float32)
        with open(meta_path, encoding="utf-8", newline="") as arquivo:
            registros = [
                PropostaEvidencia(
                    nome=linha["nome"].strip(),
                    municipio=linha["municipio"].strip(),
                    tipo=(linha.get("tipo") or "").strip() or None,
                    numero=_inteiro_ou_none(linha.get("numero")),
                    ano=_inteiro_ou_none(linha.get("ano")),
                    resumo=linha["resumo"].strip(),
                )
                for linha in csv.DictReader(arquivo)
            ]
        if vetores.ndim != 2 or vetores.shape[1] != settings.embedding_dim:
            raise ValueError(f"shape inválido: {vetores.shape}")
        if len(vetores) != len(registros):
            raise ValueError(
                f"artefatos desalinhados: {len(vetores)} vetores, {len(registros)} metadados"
            )
        if not np.isfinite(vetores).all():
            raise ValueError("embeddings de propostas contêm valores não finitos")
        return vetores, registros
    except (OSError, ValueError, KeyError) as exc:
        logger.warning("Evidências da recomendação indisponíveis: %s", exc)
        return np.empty((0, settings.embedding_dim), dtype=np.float32), []


def gerar_embedding(texto: str) -> list[float]:
    """Projeta o texto do cidadão no espaço 768d dos perfis dos políticos.

    BERT (norma L2 = 1) → subtrai o centróide do corpus → re-normaliza L2. Mesma
    transformação dos perfis (sem a média sobre N propostas, pois a query é um texto só).
    """
    vec = _modelo().encode([texto], normalize_embeddings=True, convert_to_numpy=True)[0]
    v = vec.astype(np.float32) - _centroide()
    norma = float(np.linalg.norm(v))
    v = v / max(norma, 1e-10)
    return v.astype(float).tolist()


def _sem_acento(palavra: str) -> str:
    return unicodedata.normalize("NFKD", palavra.lower()).encode("ascii", "ignore").decode()


def _temas_do_resumo(resumo: str) -> list[str]:
    """Temas municipais (whitelist) presentes no resumo, na ordem de aparição.

    Retorna a palavra ORIGINAL (acentuada) p/ exibição; o casamento é sem acento.
    """
    temas: list[str] = []
    for palavra in re.findall(r"[A-Za-zÀ-ÿ]+", resumo.lower()):
        if _sem_acento(palavra) in TEMAS_CONHECIDOS and palavra not in temas:
            temas.append(palavra)
    return temas


def evidencias_para_politico(
    vetor: list[float],
    politico: Politico,
    limite: int = 2,
) -> list[PropostaEvidencia]:
    """Seleciona as propostas do político semanticamente mais próximas da query.

    A query (vetor de interesses, já projetado) e as propostas vivem no mesmo espaço
    centrado do SBERT; o produto escalar é o cosseno. Só retorna propostas acima do piso
    de relevância — se nem a melhor passar, não inventa evidência (devolve lista vazia).
    """
    if limite <= 0:
        return []
    vetores, registros = _base_evidencias()
    if not registros:
        return []

    query = np.asarray(vetor, dtype=np.float32)
    if query.shape != (settings.embedding_dim,) or not np.isfinite(query).all():
        return []

    chave = ((politico.municipio or "").strip(), politico.nome.strip())
    indices = [
        i for i, proposta in enumerate(registros) if (proposta.municipio, proposta.nome) == chave
    ]
    if not indices:
        return []

    scores = vetores[indices] @ query  # cosseno semântico (vetores já projetados)
    ordem = np.argsort(-scores, kind="stable")[:limite]
    melhor = float(scores[int(ordem[0])])
    if melhor < EVIDENCE_MIN_SCORE:
        return []  # nada do político é realmente sobre a query → sem evidência
    selecionados = [
        int(i)
        for i in ordem
        if float(scores[int(i)]) >= EVIDENCE_MIN_SCORE
        and melhor - float(scores[int(i)]) <= MAX_EVIDENCE_SCORE_GAP
    ]
    return [registros[indices[i]] for i in selecionados]


def justificativa_para(politico: Politico, evidencias: list[PropostaEvidencia]) -> str | None:
    """Frase específica citando os TEMAS reais das propostas (não genérica nem com verbos)."""
    if not evidencias:
        return None
    temas: list[str] = []
    for evidencia in evidencias:
        for tema in _temas_do_resumo(evidencia.resumo):
            if tema not in temas:
                temas.append(tema)
    primeiro_nome = (politico.nome or "").split()[0] if politico.nome else "Esse vereador"
    if temas:
        return f"{primeiro_nome} propôs matérias sobre {', '.join(temas[:2])}, alinhadas às suas pautas:"
    return f"Matérias de {primeiro_nome} mais próximas das suas pautas:"


_LLM_SYSTEM = (
    "Você explica, em português do Brasil, por que um vereador combina com as pautas de um "
    "cidadão. Para cada vereador, escreva UMA frase curta (no máximo 24 palavras), natural e "
    "específica, citando concretamente o que ele propôs — baseando-se SOMENTE nas propostas "
    "fornecidas, sem inventar nada. Conecte com as pautas do cidadão. Evite clichês como "
    "'alinhado às suas pautas'. Responda APENAS um JSON no formato "
    '{"0": "frase", "1": "frase"}, usando exatamente os índices recebidos.'
)


@lru_cache(maxsize=1)
def _groq_client():
    """Cliente Groq (criado uma vez). Import tardio; dependência leve."""
    from groq import Groq

    return Groq(api_key=settings.groq_api_key, timeout=settings.llm_timeout_seconds)


def justificativas_llm(
    pautas: str,
    itens: list[tuple[Politico, list[PropostaEvidencia]]],
) -> dict[UUID, str]:
    """Gera, em UMA chamada batched ao LLM, uma justificativa sob medida por vereador.

    Mapeia `politico.id -> frase`. Degrada para `{}` (silencioso) se não houver chave/itens
    ou em qualquer falha/timeout — o chamador então usa o texto-base (`justificativa_para`).
    """
    if not settings.groq_api_key or not itens:
        return {}
    vereadores = {
        str(i): {"nome": p.nome, "propostas": [e.resumo for e in evs]}
        for i, (p, evs) in enumerate(itens)
    }
    entrada = json.dumps({"pautas": pautas, "vereadores": vereadores}, ensure_ascii=False)
    try:
        resp = _groq_client().chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": _LLM_SYSTEM},
                {"role": "user", "content": entrada},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1000,
        )
        bruto = json.loads(resp.choices[0].message.content or "{}")
        mapa = bruto.get("justificativas", bruto) if isinstance(bruto, dict) else {}
        resultado: dict[UUID, str] = {}
        for chave, frase in mapa.items() if isinstance(mapa, dict) else []:
            try:
                idx = int(chave)
            except (TypeError, ValueError):
                continue
            texto = str(frase).strip()
            if texto and 0 <= idx < len(itens):
                resultado[itens[idx][0].id] = texto
        return resultado
    except Exception as exc:  # noqa: BLE001 - LLM é best-effort; cai no texto-base
        logger.warning("Justificativa LLM (Groq) indisponível: %s", exc)
        return {}


def warmup() -> None:
    """Pré-carrega modelo e centróide (chamado no startup p/ evitar cold start)."""
    _modelo()
    _centroide()
    _base_evidencias()


def top_politicos_por_similaridade(
    db: Session, vetor: list[float], limite: int = 10
) -> list[tuple[Politico, float]]:
    """Retorna os políticos mais próximos do vetor de interesses por cosseno.

    `cosine_distance` ∈ [0, 2]; convertemos para um score de similaridade (1 - dist).
    Só retorna políticos que já têm embedding populado.
    """
    distancia = Politico.embedding.cosine_distance(vetor)
    stmt = (
        select(Politico, distancia.label("dist"))
        .where(Politico.embedding.isnot(None))
        .order_by(distancia)
        .limit(limite)
    )
    return [(pol, 1.0 - float(dist)) for pol, dist in db.execute(stmt).all()]


def cluster_alinhado(matches: list[tuple[Politico, float]]) -> int | None:
    """Cluster (k-means) do político mais bem ranqueado, se houver."""
    for politico, _score in matches:
        if politico.cluster_id is not None:
            return politico.cluster_id
    return None
