from uuid import UUID

from pydantic import BaseModel, Field


class InteressesIn(BaseModel):
    """Texto livre / tags com as pautas que o cidadão mais engaja."""

    texto: str = Field(min_length=1)


class PoliticoMatch(BaseModel):
    id: UUID
    nome: str
    cargo: str | None
    partido: str | None
    municipio: str | None
    resumo_llm: str | None
    cluster_id: int | None
    # Similaridade de cosseno (1.0 = idêntico). None enquanto não há embeddings.
    score: float | None


class RecomendacaoOut(BaseModel):
    # True quando ainda não há embeddings populados (pipeline do colega) ou o usuário
    # não definiu interesses — o front trata como estado vazio/placeholder.
    placeholder: bool
    top_politicos: list[PoliticoMatch] = []
    cluster_alinhado: int | None = None
