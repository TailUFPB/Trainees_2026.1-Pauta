from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PublicacaoCriarIn(BaseModel):
    conteudo: str = Field(min_length=1, max_length=1000)
    anonimo: bool = False
    imagem_url: str | None = None  # MVP: upload separado fica pra próxima fatia

    @field_validator("conteudo")
    @classmethod
    def _conteudo_nao_so_whitespace(cls, v: str) -> str:
        # min_length=1 não pega "   ": o router faz .strip() antes do INSERT
        # e o CHECK do banco rejeitaria com 500. Falhamos cedo, em 422.
        if not v.strip():
            raise ValueError("conteudo não pode ser só espaços em branco")
        return v


class PublicacaoOut(BaseModel):
    id: UUID
    conteudo: str
    imagem_url: str | None
    anonimo: bool
    autor_nome: str | None
    created_at: datetime
