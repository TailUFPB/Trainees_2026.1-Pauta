from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PublicacaoCriarIn(BaseModel):
    conteudo: str = Field(min_length=1, max_length=1000)
    anonimo: bool = False
    imagem_url: str | None = None  # MVP: upload separado fica pra próxima fatia


class PublicacaoOut(BaseModel):
    id: UUID
    conteudo: str
    imagem_url: str | None
    anonimo: bool
    autor_nome: str | None
    created_at: datetime
