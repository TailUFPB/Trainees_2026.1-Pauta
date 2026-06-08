"""expand ck_outbox_tipo

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-03

Amplia ck_outbox_tipo (definida em 0001) para acomodar novos tipos de evento
sem precisar de migration ad-hoc dentro de hotfix.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_TIPOS_AMPLIADOS = (
    "problema.criado",
    "problema.status_alterado",
    "politico.status_alterado",
    "politico.atualizado",
    "usuario.atualizado",
)


def upgrade() -> None:
    op.execute("ALTER TABLE eventos_outbox DROP CONSTRAINT ck_outbox_tipo")
    valores = ", ".join(f"'{t}'" for t in _TIPOS_AMPLIADOS)
    op.execute(
        f"ALTER TABLE eventos_outbox ADD CONSTRAINT ck_outbox_tipo "
        f"CHECK (tipo IN ({valores}))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE eventos_outbox DROP CONSTRAINT ck_outbox_tipo")
    op.execute(
        "ALTER TABLE eventos_outbox ADD CONSTRAINT ck_outbox_tipo "
        "CHECK (tipo IN ('problema.criado','problema.status_alterado',"
        "'politico.status_alterado'))"
    )
