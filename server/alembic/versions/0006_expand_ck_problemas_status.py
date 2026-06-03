"""expand ck_problemas_status

Revision ID: 0006
Revises: 0002
Create Date: 2026-06-03

Amplia os valores aceitos por ck_problemas_status (definida em 0001) para
incluir 'arquivado' e 'cancelado' — estados comuns em workflows de denúncia
que faltavam e gerariam check_violation em 500 silencioso.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0006"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE problemas DROP CONSTRAINT ck_problemas_status")
    op.execute(
        "ALTER TABLE problemas ADD CONSTRAINT ck_problemas_status "
        "CHECK (status IN ('aberto','em_andamento','resolvido','arquivado','cancelado'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE problemas DROP CONSTRAINT ck_problemas_status")
    op.execute(
        "ALTER TABLE problemas ADD CONSTRAINT ck_problemas_status "
        "CHECK (status IN ('aberto','em_andamento','resolvido'))"
    )
