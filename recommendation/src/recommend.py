# RECOMENDAÇÃO (demonstração offline)
#
# Função principal do pipeline offline: dado um texto livre de pautas do cidadão,
# ranqueia os vereadores por alinhamento temático (similaridade de cosseno).
#
# IMPORTANTE — fonte única de verdade do espaço vetorial:
#   embed_query() projeta a query EXATAMENTE como os perfis foram projetados
#   (BERT normalizado -> projetar_no_espaco = subtrai o MESMO centróide + re-normaliza L2).
#   Esta é a mesma transformação reaproveitada de embeddings.py. O backend
#   (server/app/services/recomendacao.py) replica esta lógica em produção (mesma transformação);
#   manter os dois caminhos sincronizados é um invariante manual.
#
# Este módulo é a DEMO/validação offline. Em produção o ranking roda no Postgres via
# pgvector (índice HNSW de cosseno) — ver server/. Aqui o ranking é um produto escalar
# em numpy contra embeddings.npy, suficiente para n=94 e usado no notebook 4.

import numpy as np
import pandas as pd
from pathlib import Path
from functools import lru_cache

from sentence_transformers import SentenceTransformer

# reaproveita a transformação canônica e os caminhos/nomes do módulo de embeddings
from embeddings import projetar_no_espaco, MODEL_NAME, MODELS_DIR

# datapath
EMBEDDINGS_PATH = MODELS_DIR / "embeddings.npy"
META_PATH = MODELS_DIR / "embeddings_meta.csv"
CLUSTERS_PATH = MODELS_DIR / "clusters.csv"
CENTROID_PATH = MODELS_DIR / "centroid.npy"


# _modelo / _centroide -> carregados uma única vez (singletons via lru_cache)
@lru_cache(maxsize=1)
def _modelo() -> SentenceTransformer:
    """Carrega o BERT português uma única vez (custo amortizado entre queries)."""
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=1)
def _centroide() -> np.ndarray:
    """Carrega o centróide do corpus (persistido por embeddings.py)."""
    if not CENTROID_PATH.exists():
        raise FileNotFoundError(
            f"Centróide não encontrado em: {CENTROID_PATH}\n"
            "Execute src/embeddings.py (versão que persiste centroid.npy) antes."
        )
    return np.load(CENTROID_PATH)


# embed_query -> texto livre do cidadão -> vetor 768d no MESMO espaço dos perfis
def embed_query(texto: str) -> np.ndarray:
    """Projeta a query do cidadão no espaço centrado dos perfis (768d, norma L2 = 1).

    É o análogo da geração de perfil — porém SEM a etapa de média sobre N propostas,
    pois a query é um único texto. A projeção (subtrair centróide + normalizar) é
    idêntica, garantindo que query e perfis vivam no mesmo espaço.
    """
    vec = _modelo().encode([texto], normalize_embeddings=True, convert_to_numpy=True)[0]
    return projetar_no_espaco(vec, _centroide())


# _carregar_perfis -> embeddings dos vereadores + metadados (com cluster, se houver)
@lru_cache(maxsize=1)
def _carregar_perfis() -> tuple[np.ndarray, pd.DataFrame]:
    emb = np.load(EMBEDDINGS_PATH)
    meta = pd.read_csv(META_PATH)
    if CLUSTERS_PATH.exists():
        clusters = pd.read_csv(CLUSTERS_PATH)
        meta = meta.merge(clusters, on=["nome", "municipio"], how="left")
    else:
        meta = meta.copy()
        meta["cluster_id"] = pd.NA
    return emb, meta


# recomendar -> ranking dos k vereadores mais alinhados ao texto do cidadão
def recomendar(texto: str, k: int = 5) -> pd.DataFrame:
    """Retorna os top-k vereadores por similaridade de cosseno com a query.

    Como query e perfis têm norma L2 = 1, o produto escalar JÁ é o cosseno.
    score ∈ [-1, 1] (1 = perfeitamente alinhado).
    """
    q = embed_query(texto)
    emb, meta = _carregar_perfis()
    scores = emb @ q  # cosseno (vetores unitários)
    idx = np.argsort(-scores)[:k]

    resultado = meta.iloc[idx].copy()
    resultado["score"] = scores[idx]
    resultado = resultado.reset_index(drop=True)
    return resultado[["nome", "municipio", "cluster_id", "score"]]


# pipeline principal -> demonstração rápida no terminal
if __name__ == "__main__":
    consultas = [
        "saúde pública, postos de saúde e atendimento médico no bairro",
        "transporte público, mobilidade urbana e proteção a ciclistas",
        "educação, creches e merenda escolar",
    ]
    for texto in consultas:
        print(f"\n=== Query: {texto!r} ===")
        print(recomendar(texto, k=5).to_string(index=False))
