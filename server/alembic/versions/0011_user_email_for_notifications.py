"""user email for notifications

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-08

Mantem uma copia operacional do email em public.users para o Notification Service.
O token FCM continua em users.prefs_notificacao->>'token_fcm'.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index(
        "ix_users_email_not_null",
        "users",
        ["email"],
        unique=False,
        postgresql_where=sa.text("email IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_email_not_null", table_name="users")
    op.drop_column("users", "email")
