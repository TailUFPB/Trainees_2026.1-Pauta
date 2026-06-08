from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ItemFeedPublicacao(BaseModel):
    tipo: Literal["publicacao"] = "publicacao"
    id: UUID
    conteudo: str
    imagem_url: str | None
    anonimo: bool
    autor_nome: str | None
    created_at: datetime


class ItemFeedProblema(BaseModel):
    tipo: Literal["problema"] = "problema"
    id: UUID
    foto_url: str | None
    lat: float
    lng: float
    tipo_problema: str | None
    severidade: str | None
    resumo_llm: str | None
    status: str
    anonimo: bool
    autor_nome: str | None
    created_at: datetime


ItemFeed = ItemFeedPublicacao | ItemFeedProblema
