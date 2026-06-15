from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TipoProblema = Literal[
    "asfalto",
    "alagamento",
    "iluminacao",
    "lixo",
    "arborizacao",
    "sinalizacao",
    "calcada",
    "esgoto",
    "outros",
    "nenhum",
]
Severidade = Literal["baixa", "media", "alta", "critica"]
StatusProblema = Literal["aberto", "em_andamento", "resolvido", "arquivado", "cancelado"]


class ClassificacaoFoto(BaseModel):
    """Saída estruturada da LLM de fotos (contrato com o módulo de visão do colega).

    Espelha o schema JSON definido no relatório da LLM de análise de fotos.
    """

    tipo_problema: TipoProblema
    severidade: Severidade
    resumo_llm: str
    palavras_chave: list[str] = Field(default_factory=list)
    modelo_utilizado: str
    confianca: float = Field(ge=0.0, le=1.0)


class ProblemaOut(BaseModel):
    id: UUID
    foto_url: str | None
    lat: float
    lng: float
    tipo_problema: TipoProblema | None
    severidade: Severidade | None
    resumo_llm: str | None
    palavras_chave: list[str]
    confianca: float | None
    modelo_utilizado: str | None
    precisa_revisao: bool
    status: StatusProblema
    resolvido_por: str | None
    resolvido_em: datetime | None
    descricao: str | None
    autor_nome: str | None  # None quando anônimo
    anonimo: bool
    created_at: datetime


class ProblemaPublicoOut(BaseModel):
    """Versão pública de um problema — oculta autor_id e descricao livre.

    Usado em GET /problemas (lista pra mapa) e em GET /problemas/{id} quando o
    solicitante não é o autor. Mantém todos os campos não-PII pra que o mapa e
    consumidores externos continuem funcionando.
    """

    id: UUID
    foto_url: str | None
    lat: float
    lng: float
    tipo_problema: TipoProblema | None
    severidade: Severidade | None
    resumo_llm: str | None
    palavras_chave: list[str]
    confianca: float | None
    modelo_utilizado: str | None
    precisa_revisao: bool
    status: StatusProblema
    resolvido_por: str | None
    resolvido_em: datetime | None
    autor_nome: str | None  # None quando anônimo
    anonimo: bool
    created_at: datetime


class AtualizarStatusIn(BaseModel):
    status: StatusProblema
    resolvido_por: str | None = None
