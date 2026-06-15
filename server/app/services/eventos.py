"""Fronteira de produção de eventos com o Notification Service.

O backend é apenas o PRODUTOR. Ele grava eventos numa tabela de outbox; o consumidor
(Notification Service — Node/BullMQ ou Python/Celery, decisão futura do time) lê os
eventos não processados, dispara push/email e marca como processados.

Manter a fronteira em dados (e não em rede) permite extrair o consumidor depois sem
tocar no resto do backend.
"""

from abc import ABC, abstractmethod
from typing import Literal

from sqlalchemy.orm import Session

from app.models.evento import EventoOutbox

TipoEvento = Literal[
    "problema.criado",
    "problema.status_alterado",
    "politico.status_alterado",
    "politico.atualizado",
    "usuario.atualizado",
    "notificacao.teste",
    "publicacao.criada",
]
Prioridade = Literal["alta", "media", "baixa"]


class EventPublisher(ABC):
    """Interface de publicação. Trocar a implementação (ex.: broker real) não afeta
    quem chama `publish`."""

    @abstractmethod
    def publish(
        self, tipo: TipoEvento, payload: dict, prioridade: Prioridade = "media"
    ) -> None: ...


class OutboxPublisher(EventPublisher):
    """Implementação padrão: persiste o evento na tabela `eventos_outbox`.

    Usa a sessão da própria request, então o evento entra na mesma transação do
    fato que o gerou (ex.: criação do problema) — sem evento órfão nem fato sem evento.
    """

    def __init__(self, db: Session):
        self.db = db

    def publish(
        self, tipo: TipoEvento, payload: dict, prioridade: Prioridade = "media"
    ) -> None:
        self.db.add(EventoOutbox(tipo=tipo, payload=payload, prioridade=prioridade))
