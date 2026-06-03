"""Seam do sistema de recomendação.

Dois pontos de contato com o módulo do colega (scraping/NLP/embeddings):

1. `gerar_embedding(texto)` — STUB. O colega liga ao mesmo modelo de embedding usado
   no pipeline offline dos políticos (a dimensão DEVE bater com EMBEDDING_DIM).
2. `top_politicos_por_similaridade(db, vetor, limite)` — query pgvector de similaridade
   de cosseno (`<=>`), já pronta. Roda dentro do Postgres; só depende dos embeddings
   dos políticos estarem populados.
"""


from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.politico import Politico

settings = get_settings()


def gerar_embedding(texto: str) -> list[float]:
    """STUB: retorna um vetor determinístico a partir do texto, só para o fluxo rodar.

    Substituir pela chamada ao modelo de embedding real (mesmo do pipeline de políticos).
    """
    import hashlib

    dim = settings.embedding_dim
    seed = hashlib.sha256(texto.encode("utf-8")).digest()
    # Expande o hash até a dimensão desejada, normalizado para [-1, 1].
    vals = [((seed[i % len(seed)] / 127.5) - 1.0) for i in range(dim)]
    return vals


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
