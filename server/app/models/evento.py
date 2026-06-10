from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Tipos de evento produzidos pelo backend e consumidos pelo Notification Service.
TIPOS_EVENTO = (
    "problema.criado",
    "problema.status_alterado",
    "politico.status_alterado",
    "politico.atualizado",
    "usuario.atualizado",
    "notificacao.teste",
)
PRIORIDADES = ("alta", "media", "baixa")


class EventoOutbox(Base):
    """Tabela de outbox — ponto de desacoplamento entre o backend (produtor de eventos)
    e o Notification Service (consumidor, dono indefinido: Node/BullMQ ou Python/Celery).

    O consumidor lê linhas com `processado_em IS NULL`, dispara as notificações e marca
    como processadas. Mantém a fronteira em dados, não em rede — fácil de extrair depois.
    """

    __tablename__ = "eventos_outbox"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    prioridade: Mapped[str] = mapped_column(String(10), default="media", server_default="media")

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tentativas: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
