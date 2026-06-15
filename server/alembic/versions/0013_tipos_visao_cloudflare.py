"""alinha tipos de problema com classificador Cloudflare

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-12
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TIPOS_NOVOS = (
    "asfalto",
    "alagamento",
    "iluminacao",
    "lixo",
    "arborizacao",
    "sinalizacao",
    "calcada",
    "esgoto",
    "outros",
    "nenhum",
)
_TIPOS_ANTIGOS = (
    "buraco",
    "alagamento",
    "entulho",
    "obstrucao_vegetacao",
    "sinalizacao_defeituosa",
    "iluminacao",
    "calcada_irregular",
    "outro",
)


def _in_list(col: str, valores: tuple[str, ...]) -> str:
    quoted = ",".join(f"'{v}'" for v in valores)
    return f"{col} IN ({quoted})"


def upgrade() -> None:
    op.execute("ALTER TABLE problemas DROP CONSTRAINT IF EXISTS ck_problemas_tipo")
    op.execute(
        """
        UPDATE problemas
        SET tipo_problema = CASE tipo_problema
            WHEN 'buraco' THEN 'asfalto'
            WHEN 'entulho' THEN 'lixo'
            WHEN 'obstrucao_vegetacao' THEN 'arborizacao'
            WHEN 'sinalizacao_defeituosa' THEN 'sinalizacao'
            WHEN 'calcada_irregular' THEN 'calcada'
            WHEN 'outro' THEN 'outros'
            ELSE tipo_problema
        END
        WHERE tipo_problema IS NOT NULL
        """
    )
    op.execute(
        "ALTER TABLE problemas ADD CONSTRAINT ck_problemas_tipo "
        f"CHECK (tipo_problema IS NULL OR {_in_list('tipo_problema', _TIPOS_NOVOS)})"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE problemas DROP CONSTRAINT IF EXISTS ck_problemas_tipo")
    op.execute(
        """
        UPDATE problemas
        SET tipo_problema = CASE tipo_problema
            WHEN 'asfalto' THEN 'buraco'
            WHEN 'lixo' THEN 'entulho'
            WHEN 'arborizacao' THEN 'obstrucao_vegetacao'
            WHEN 'sinalizacao' THEN 'sinalizacao_defeituosa'
            WHEN 'calcada' THEN 'calcada_irregular'
            WHEN 'esgoto' THEN 'outro'
            WHEN 'outros' THEN 'outro'
            WHEN 'nenhum' THEN 'outro'
            ELSE tipo_problema
        END
        WHERE tipo_problema IS NOT NULL
        """
    )
    op.execute(
        "ALTER TABLE problemas ADD CONSTRAINT ck_problemas_tipo "
        f"CHECK (tipo_problema IS NULL OR {_in_list('tipo_problema', _TIPOS_ANTIGOS)})"
    )
