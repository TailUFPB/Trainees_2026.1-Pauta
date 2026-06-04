from datetime import datetime
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.schemas.problema import Severidade, StatusProblema, TipoProblema


class Problema(Base):
    """Problema de infraestrutura reportado por um cidadão, com localização (PostGIS)."""

    __tablename__ = "problemas"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # HMAC-SHA256 do user.id do autor. Calculado por app.core.hmac_autor.autor_hmac.
    # Substitui a antiga FK autor_id desde a migration 0010 — pseudonimiza autoria.
    autor_hmac: Mapped[bytes | None] = mapped_column(LargeBinary)

    foto_url: Mapped[str | None] = mapped_column(String(1024))

    # Geometria do ponto reportado. Índice GIST criado na migration.
    localizacao: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )

    # Saída estruturada da LLM de fotos.
    tipo_problema: Mapped[TipoProblema | None] = mapped_column(String(40))
    severidade: Mapped[Severidade | None] = mapped_column(String(20))
    resumo_llm: Mapped[str | None] = mapped_column(String)
    palavras_chave: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list, server_default="{}"
    )
    confianca: Mapped[float | None] = mapped_column(Float)
    modelo_utilizado: Mapped[str | None] = mapped_column(String(80))
    precisa_revisao: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    status: Mapped[StatusProblema] = mapped_column(
        String(20), default="aberto", server_default="aberto"
    )
    resolvido_por: Mapped[str | None] = mapped_column(String(160))
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    descricao: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
