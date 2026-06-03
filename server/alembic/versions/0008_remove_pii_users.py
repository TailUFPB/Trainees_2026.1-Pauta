"""remove pii de users

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-03

Remove colunas nome e email de users. O email já existe no auth.users do
Supabase (fonte da verdade); manter cópia local é PII redundante. O front
passa a ler o email diretamente da sessão Supabase via getServerSession().
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "nome")
    op.drop_column("users", "email")


def downgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("nome", sa.String(length=120), nullable=True))
