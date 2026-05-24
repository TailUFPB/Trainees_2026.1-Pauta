"""initial schema: extensoes (postgis, pgvector) + tabelas

Revision ID: 0001
Revises:
Create Date: 2026-05-26
"""
from typing import Sequence, Union

import geoalchemy2
import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.config import get_settings

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = get_settings().embedding_dim


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(120)),
        sa.Column("email", sa.String(255)),
        sa.Column(
            "localizacao",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        ),
        sa.Column("interesses_vetor", pgvector.sqlalchemy.Vector(EMBEDDING_DIM)),
        sa.Column("prefs_notificacao", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "politicos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(160), nullable=False),
        sa.Column("cargo", sa.String(80)),
        sa.Column("partido", sa.String(40)),
        sa.Column("municipio", sa.String(120)),
        sa.Column("resumo_llm", sa.String()),
        sa.Column("palavras_chave", postgresql.ARRAY(sa.String()), server_default="{}"),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(EMBEDDING_DIM)),
        sa.Column("cluster_id", sa.Integer()),
        sa.Column("fonte_url", sa.String(1024)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "problemas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("autor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("foto_url", sa.String(1024)),
        sa.Column(
            "localizacao",
            geoalchemy2.Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("tipo_problema", sa.String(40)),
        sa.Column("severidade", sa.String(20)),
        sa.Column("resumo_llm", sa.String()),
        sa.Column("palavras_chave", postgresql.ARRAY(sa.String()), server_default="{}"),
        sa.Column("confianca", sa.Float()),
        sa.Column("modelo_utilizado", sa.String(80)),
        sa.Column("precisa_revisao", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", sa.String(20), server_default="aberto", nullable=False),
        sa.Column("resolvido_por", sa.String(160)),
        sa.Column("resolvido_em", sa.DateTime(timezone=True)),
        sa.Column("descricao", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Índice espacial GIST para consultas por bbox/raio no mapa.
    op.create_index(
        "ix_problemas_localizacao",
        "problemas",
        ["localizacao"],
        postgresql_using="gist",
    )

    op.create_table(
        "inscricoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("problema_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problemas.id")),
        sa.Column(
            "regiao",
            geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
        ),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "seguidores_politico",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("politico_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("politicos.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "politico_id", name="uq_seguidor_politico"),
    )

    op.create_table(
        "eventos_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("prioridade", sa.String(10), server_default="media", nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("processado_em", sa.DateTime(timezone=True)),
        sa.Column("tentativas", sa.Integer(), server_default="0", nullable=False),
    )
    # Consumidor varre os não-processados por ordem de chegada.
    op.create_index(
        "ix_eventos_outbox_pendentes",
        "eventos_outbox",
        ["criado_em"],
        postgresql_where=sa.text("processado_em IS NULL"),
    )

    # Índice HNSW para similaridade de cosseno na recomendação (não exige treino prévio).
    op.create_index(
        "ix_politicos_embedding",
        "politicos",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_politicos_embedding", table_name="politicos")
    op.drop_index("ix_eventos_outbox_pendentes", table_name="eventos_outbox")
    op.drop_table("eventos_outbox")
    op.drop_table("seguidores_politico")
    op.drop_table("inscricoes")
    op.drop_index("ix_problemas_localizacao", table_name="problemas")
    op.drop_table("problemas")
    op.drop_table("politicos")
    op.drop_table("users")
