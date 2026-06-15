from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.base import Base

EMBEDDING_DIM = get_settings().embedding_dim


class User(Base):
    """Usuário da plataforma. `id` espelha o `auth.users.id` do Supabase Auth.

    O email é mantido localmente para o Notification Service encontrar
    destinatários sem depender da API de Auth durante o processamento da fila.
    O nome público é exibido no feed quando a publicação não é anônima.
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255))

    # Nome exibido no feed quando publicação não-anônima.
    # Default = parte local do e-mail; usuário pode personalizar em /conta/perfil (futuro).
    nome_publico: Mapped[str | None] = mapped_column(String(120))

    # Localização "de casa" usada para os geo-alertas de proximidade.
    localizacao: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    # Vetor de interesses do cidadão, base da recomendação por similaridade de cosseno.
    # Populado a partir de POST /usuarios/me/interesses (embedding gerado pelo serviço).
    interesses_vetor: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    # Preferências de canais/níveis de notificação (consumido pelo Notification Service).
    prefs_notificacao: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
