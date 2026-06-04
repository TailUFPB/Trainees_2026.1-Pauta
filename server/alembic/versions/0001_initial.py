"""initial schema: extensoes, tabelas, indices, CHECKs, FK auth e RLS

Inclui defesa em profundidade: RLS habilitada em todas as tabelas do `public`
(o backend conecta como role privilegiada, então segue funcionando; bloqueia
acesso indevido via Data API do Supabase com a anon key).

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

_TIPOS_PROBLEMA = (
    "buraco",
    "alagamento",
    "entulho",
    "obstrucao_vegetacao",
    "sinalizacao_defeituosa",
    "iluminacao",
    "calcada_irregular",
    "outro",
)
_SEVERIDADES = ("baixa", "media", "alta", "critica")
_STATUS_PROBLEMA = ("aberto", "em_andamento", "resolvido")
_TIPOS_INSCRICAO = ("problema", "regiao")
_TIPOS_EVENTO = ("problema.criado", "problema.status_alterado", "politico.status_alterado")
_PRIORIDADES = ("alta", "media", "baixa")


def _in_list(col: str, valores: tuple[str, ...]) -> str:
    quoted = ",".join(f"'{v}'" for v in valores)
    return f"{col} IN ({quoted})"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ------------------------------------------------------------------ users
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
    # GIST: usado por geo-alertas de proximidade (consumidor de notificações).
    op.create_index("ix_users_localizacao", "users", ["localizacao"], postgresql_using="gist")
    # FK pra auth.users só existe em ambiente Supabase. Local/CI não tem schema `auth`.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'auth' AND table_name = 'users'
            ) THEN
                ALTER TABLE public.users
                    ADD CONSTRAINT users_id_auth_users_fkey
                    FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
            END IF;
        END $$;
        """
    )

    # -------------------------------------------------------------- politicos
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
    # HNSW parcial: só políticos com embedding entram (mantém o índice enxuto enquanto
    # o pipeline offline do colega ainda não populou todo mundo).
    op.execute(
        """
        CREATE INDEX ix_politicos_embedding ON politicos
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL
        """
    )

    # -------------------------------------------------------------- problemas
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
        sa.CheckConstraint(
            f"tipo_problema IS NULL OR {_in_list('tipo_problema', _TIPOS_PROBLEMA)}",
            name="ck_problemas_tipo",
        ),
        sa.CheckConstraint(
            f"severidade IS NULL OR {_in_list('severidade', _SEVERIDADES)}",
            name="ck_problemas_severidade",
        ),
        sa.CheckConstraint(_in_list("status", _STATUS_PROBLEMA), name="ck_problemas_status"),
    )
    # GIST: filtro por bbox no mapa.
    op.create_index(
        "ix_problemas_localizacao", "problemas", ["localizacao"], postgresql_using="gist"
    )
    # FK index → joins e ON DELETE CASCADE rápidos.
    op.create_index("ix_problemas_autor_id", "problemas", ["autor_id"])
    # Feed: GET /problemas filtra por status e ordena por created_at DESC.
    op.execute(
        "CREATE INDEX ix_problemas_status_created_at "
        "ON problemas (status, created_at DESC)"
    )

    # -------------------------------------------------------------- inscricoes
    op.create_table(
        "inscricoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("problema_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problemas.id")),
        sa.Column(
            "regiao",
            geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
        ),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(_in_list("tipo", _TIPOS_INSCRICAO), name="ck_inscricoes_tipo"),
        # Inscrição é OU em um problema específico OU em uma região (XOR).
        sa.CheckConstraint(
            "(problema_id IS NULL) != (regiao IS NULL)",
            name="ck_inscricoes_alvo_unico",
        ),
    )
    op.create_index("ix_inscricoes_user_id", "inscricoes", ["user_id"])
    op.create_index("ix_inscricoes_problema_id", "inscricoes", ["problema_id"])
    # GIST parcial — só inscrições de região têm geometria; ponto-em-polígono no consumer.
    op.execute(
        "CREATE INDEX ix_inscricoes_regiao ON inscricoes USING gist (regiao) "
        "WHERE regiao IS NOT NULL"
    )

    # ----------------------------------------------------- seguidores_politico
    op.create_table(
        "seguidores_politico",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "politico_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("politicos.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "politico_id", name="uq_seguidor_politico"),
    )
    # UNIQUE (user_id, politico_id) já cobre lookups por user_id (leftmost prefix).
    # Falta o lado oposto: "quem segue este político".
    op.create_index(
        "ix_seguidores_politico_politico_id",
        "seguidores_politico",
        ["politico_id"],
    )

    # ---------------------------------------------------------- eventos_outbox
    op.create_table(
        "eventos_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("prioridade", sa.String(10), server_default="media", nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("processado_em", sa.DateTime(timezone=True)),
        sa.Column("tentativas", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint(_in_list("tipo", _TIPOS_EVENTO), name="ck_outbox_tipo"),
        sa.CheckConstraint(_in_list("prioridade", _PRIORIDADES), name="ck_outbox_prioridade"),
    )
    # Outbox tem churn alto (INSERT + UPDATE p/ marcar processado). fillfactor menor
    # deixa espaço pra HOT updates e reduz bloat do índice parcial.
    op.execute("ALTER TABLE eventos_outbox SET (fillfactor = 80)")
    # Composto parcial: consumidor faz UMA query por nível ('alta'→'media'→'baixa'),
    # cada uma com SELECT ... FOR UPDATE SKIP LOCKED ORDER BY criado_em LIMIT N.
    op.execute(
        "CREATE INDEX ix_eventos_outbox_pendentes "
        "ON eventos_outbox (prioridade, criado_em) "
        "WHERE processado_em IS NULL"
    )

    # -------------------------------------------------------- RLS (defesa em profundidade)
    # `public` é exposto pelo PostgREST do Supabase por padrão. Sem RLS, qualquer um
    # com a anon key (que está no client) consegue ler tudo via Data API. Habilitamos
    # RLS sem polícias → bloqueia anon/authenticated. O backend (role privilegiada
    # `postgres` no Supabase / `pauta` superuser no docker local) bypassa RLS, segue normal.
    for tbl in (
        "users",
        "politicos",
        "problemas",
        "inscricoes",
        "seguidores_politico",
        "eventos_outbox",
    ):
        op.execute(f"ALTER TABLE public.{tbl} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for tbl in (
        "eventos_outbox",
        "seguidores_politico",
        "inscricoes",
        "problemas",
        "politicos",
        "users",
    ):
        op.execute(f"ALTER TABLE public.{tbl} DISABLE ROW LEVEL SECURITY")

    op.execute("DROP INDEX IF EXISTS ix_eventos_outbox_pendentes")
    op.drop_table("eventos_outbox")

    op.drop_index("ix_seguidores_politico_politico_id", table_name="seguidores_politico")
    op.drop_table("seguidores_politico")

    op.execute("DROP INDEX IF EXISTS ix_inscricoes_regiao")
    op.drop_index("ix_inscricoes_problema_id", table_name="inscricoes")
    op.drop_index("ix_inscricoes_user_id", table_name="inscricoes")
    op.drop_table("inscricoes")

    op.execute("DROP INDEX IF EXISTS ix_problemas_status_created_at")
    op.drop_index("ix_problemas_autor_id", table_name="problemas")
    op.drop_index("ix_problemas_localizacao", table_name="problemas")
    op.drop_table("problemas")

    op.execute("DROP INDEX IF EXISTS ix_politicos_embedding")
    op.drop_table("politicos")

    op.drop_index("ix_users_localizacao", table_name="users")
    op.drop_table("users")
