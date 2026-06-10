from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notificacao(Base):
    """Notificacao interna exibida no sino/central do usuario."""

    __tablename__ = "notificacoes"
    __table_args__ = (
        UniqueConstraint(
            "origem_evento_id",
            "user_id",
            "tipo",
            name="uq_notificacoes_evento_usuario_tipo",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    origem_evento_id: Mapped[UUID | None] = mapped_column(index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(160), nullable=False)
    mensagem: Mapped[str] = mapped_column(String, nullable=False)
    link_destino: Mapped[str | None] = mapped_column(String(1024))
    lida: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    canais: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    dados: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
