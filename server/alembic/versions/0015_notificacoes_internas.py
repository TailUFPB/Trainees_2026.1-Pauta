"""notificacoes internas

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-09

Cria a central interna de notificacoes do usuario. Email e push continuam como
canais externos opcionais; esta tabela garante historico dentro do app.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TIPOS_EVENTO = (
    "problema.criado",
    "problema.status_alterado",
    "politico.status_alterado",
    "politico.atualizado",
    "usuario.atualizado",
    "publicacao.criada",
    "notificacao.teste",
)


def _atualizar_constraint_eventos(tipos: tuple[str, ...]) -> None:
    op.execute("ALTER TABLE eventos_outbox DROP CONSTRAINT ck_outbox_tipo")
    valores = ", ".join(f"'{tipo}'" for tipo in tipos)
    op.execute(
        f"ALTER TABLE eventos_outbox ADD CONSTRAINT ck_outbox_tipo "
        f"CHECK (tipo IN ({valores}))"
    )


def upgrade() -> None:
    _atualizar_constraint_eventos(_TIPOS_EVENTO)
    op.create_table(
        "notificacoes",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("origem_evento_id", sa.Uuid(), nullable=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("titulo", sa.String(length=160), nullable=False),
        sa.Column("mensagem", sa.String(), nullable=False),
        sa.Column("link_destino", sa.String(length=1024), nullable=True),
        sa.Column("lida", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "canais",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "dados",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("lida_em", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "origem_evento_id",
            "user_id",
            "tipo",
            name="uq_notificacoes_evento_usuario_tipo",
        ),
    )
    op.create_index(
        "ix_notificacoes_origem_evento_id",
        "notificacoes",
        ["origem_evento_id"],
    )
    op.execute(
        "CREATE INDEX ix_notificacoes_user_created "
        "ON notificacoes (user_id, created_at DESC)"
    )
    op.create_index(
        "ix_notificacoes_user_nao_lidas",
        "notificacoes",
        ["user_id"],
        postgresql_where=sa.text("lida = false"),
    )

    op.execute("ALTER TABLE notificacoes ENABLE ROW LEVEL SECURITY")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                CREATE ROLE authenticated NOLOGIN;
            END IF;
        END $$;
    """)
    op.execute(
        "CREATE POLICY notificacoes_self_read ON notificacoes "
        "FOR SELECT TO authenticated USING (user_id = auth.uid())"
    )
    op.execute(
        "CREATE POLICY notificacoes_self_update ON notificacoes "
        "FOR UPDATE TO authenticated USING (user_id = auth.uid()) "
        "WITH CHECK (user_id = auth.uid())"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS notificacoes_self_update ON notificacoes")
    op.execute("DROP POLICY IF EXISTS notificacoes_self_read ON notificacoes")
    op.drop_index("ix_notificacoes_user_nao_lidas", table_name="notificacoes")
    op.drop_index("ix_notificacoes_user_created", table_name="notificacoes")
    op.drop_index("ix_notificacoes_origem_evento_id", table_name="notificacoes")
    op.drop_table("notificacoes")
    _atualizar_constraint_eventos(_TIPOS_EVENTO[:-1])
