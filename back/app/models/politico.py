from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.base import Base

EMBEDDING_DIM = get_settings().embedding_dim


class Politico(Base):
    """Político com perfil vetorizado. `embedding` e `cluster_id` são populados pelo
    pipeline offline de scraping/NLP/recomendação (responsabilidade de outro colega)."""

    __tablename__ = "politicos"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(80))
    partido: Mapped[str | None] = mapped_column(String(40))
    municipio: Mapped[str | None] = mapped_column(String(120))

    resumo_llm: Mapped[str | None] = mapped_column(String)
    palavras_chave: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list, server_default="{}"
    )

    # Embedding do perfil — base da similaridade de cosseno (índice na migration).
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    # Cluster temático atribuído pelo k-means.
    cluster_id: Mapped[int | None] = mapped_column(Integer)

    fonte_url: Mapped[str | None] = mapped_column(String(1024))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
