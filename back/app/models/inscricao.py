from datetime import datetime
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Inscricao(Base):
    """Interesse de um usuário/solvedor num problema específico ou numa região.

    Usado pelo Notification Service para descobrir quem alertar. `problema_id` e
    `regiao` são mutuamente complementares: um dos dois define o alvo do interesse.
    """

    __tablename__ = "inscricoes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    problema_id: Mapped[UUID | None] = mapped_column(ForeignKey("problemas.id"))
    regiao: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False)
    )
    # ex.: "problema" (segue um problema) | "regiao" (segue uma área)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SeguidorPolitico(Base):
    """Relação N:N: usuário segue um político (alertas de status/notícia)."""

    __tablename__ = "seguidores_politico"
    __table_args__ = (UniqueConstraint("user_id", "politico_id", name="uq_seguidor_politico"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    politico_id: Mapped[UUID] = mapped_column(ForeignKey("politicos.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
