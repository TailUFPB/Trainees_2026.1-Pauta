"""publicacoes (timeline social) + amplia ck_outbox_tipo

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-08

Cria a tabela publicacoes (post livre da timeline) com cifra reversível do
autor (esquema espelhado de problemas após 0011):
- autor_cifrado (bytea, pgp_sym_encrypt) — decifrável para exibição do nome
- autor_lookup (bytea, HMAC determinístico, indexado) — para autorização
- anonimo (bool) — quando true, autor_cifrado e autor_lookup ficam NULL

CHECK constraint garante coerência (anonimo=true → ambos NULL; anonimo=false →
ambos NOT NULL).

Amplia ck_outbox_tipo com 'publicacao.criada' (novo tipo de evento), preservando
os tipos já admitidos por 0007.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tipos vigentes ao final de 0007 — preservar no downgrade.
_TIPOS_BASE = (
    "problema.criado",
    "problema.status_alterado",
    "politico.status_alterado",
    "politico.atualizado",
    "usuario.atualizado",
)
_TIPOS_AMPLIADOS = _TIPOS_BASE + ("publicacao.criada",)


def upgrade() -> None:
    op.create_table(
        "publicacoes",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("autor_cifrado", sa.LargeBinary(), nullable=True),
        sa.Column("autor_lookup", sa.LargeBinary(), nullable=True),
        sa.Column(
            "anonimo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("conteudo", sa.String(1000), nullable=False),
        sa.Column("imagem_url", sa.String(1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(conteudo) >= 1",
            name="ck_publicacoes_conteudo_nao_vazio",
        ),
        sa.CheckConstraint(
            "(anonimo = true AND autor_cifrado IS NULL AND autor_lookup IS NULL) "
            "OR (anonimo = false AND autor_cifrado IS NOT NULL AND autor_lookup IS NOT NULL)",
            name="ck_publicacoes_autor_coerente",
        ),
    )
    op.create_index("ix_publicacoes_autor_lookup", "publicacoes", ["autor_lookup"])
    op.create_index("ix_publicacoes_created_at", "publicacoes", ["created_at"])

    # Amplia ck_outbox_tipo com 'publicacao.criada' preservando os tipos de 0007.
    op.execute("ALTER TABLE eventos_outbox DROP CONSTRAINT IF EXISTS ck_outbox_tipo")
    valores = ", ".join(f"'{t}'" for t in _TIPOS_AMPLIADOS)
    op.execute(
        f"ALTER TABLE eventos_outbox ADD CONSTRAINT ck_outbox_tipo "
        f"CHECK (tipo IN ({valores}))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE eventos_outbox DROP CONSTRAINT IF EXISTS ck_outbox_tipo")
    valores = ", ".join(f"'{t}'" for t in _TIPOS_BASE)
    op.execute(
        f"ALTER TABLE eventos_outbox ADD CONSTRAINT ck_outbox_tipo "
        f"CHECK (tipo IN ({valores}))"
    )
    op.drop_index("ix_publicacoes_created_at", table_name="publicacoes")
    op.drop_index("ix_publicacoes_autor_lookup", table_name="publicacoes")
    op.drop_table("publicacoes")
