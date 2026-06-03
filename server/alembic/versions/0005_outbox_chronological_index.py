"""outbox chronological index

Revision ID: 0005
Revises: 0002
Create Date: 2026-06-03

ix_eventos_outbox_pendentes (prioridade, criado_em) só serve queries que
filtram por prioridade. Consumo puramente cronológico (ORDER BY criado_em)
cai em seq scan + sort sob carga.

Adiciona índice complementar (criado_em) WHERE processado_em IS NULL,
preservando o composite original.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0005"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_eventos_outbox_pendentes_criado_em "
        "ON eventos_outbox (criado_em) "
        "WHERE processado_em IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_eventos_outbox_pendentes_criado_em")
