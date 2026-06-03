"""politicos unique nulls not distinct

Revision ID: 0004
Revises: 0002
Create Date: 2026-06-03

Re-cria ux_politicos_municipio_nome com NULLS NOT DISTINCT (PG 15+, ambiente
roda PG 16). Sem o flag, NULL != NULL no índice único e o seed via
ON CONFLICT (municipio, nome) duplicava linhas a cada execução para CSVs
com municipio vazio.

Antes de recriar, deduplica linhas existentes com mesma (municipio, nome) — usa
IS NOT DISTINCT FROM para também tratar NULLs como iguais.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0004"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM politicos a USING politicos b
        WHERE a.id > b.id
          AND a.nome IS NOT DISTINCT FROM b.nome
          AND a.municipio IS NOT DISTINCT FROM b.municipio
        """
    )
    op.execute("DROP INDEX IF EXISTS ux_politicos_municipio_nome")
    op.execute(
        "CREATE UNIQUE INDEX ux_politicos_municipio_nome "
        "ON politicos (municipio, nome) NULLS NOT DISTINCT"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_politicos_municipio_nome")
    op.execute(
        "CREATE UNIQUE INDEX ux_politicos_municipio_nome "
        "ON politicos (municipio, nome)"
    )
