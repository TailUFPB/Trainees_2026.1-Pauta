"""politicos.foto_url + unique (municipio, nome)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("politicos", sa.Column("foto_url", sa.String(1024), nullable=True))
    op.create_index(
        "ux_politicos_municipio_nome",
        "politicos",
        ["municipio", "nome"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_politicos_municipio_nome", table_name="politicos")
    op.drop_column("politicos", "foto_url")
