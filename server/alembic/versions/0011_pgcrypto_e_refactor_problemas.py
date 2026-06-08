"""pgcrypto + refactor autor em problemas + nome_publico em users

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-08

Substitui `autor_hmac` (one-way) por duas colunas:
- `autor_cifrado` (bytea) — pgp_sym_encrypt do user_id, decifrável pra exibição.
- `autor_lookup` (bytea, indexado) — HMAC determinístico pra autorização e
  consultas tipo "minhas publicações".

Adiciona coluna `anonimo` (bool) — quando true, ambas as colunas acima ficam NULL.

Habilita extensão pgcrypto. Adiciona `users.nome_publico` (display do autor no feed).

ATENÇÃO downgrade: recria `autor_hmac` vazio. Dados de autoria são perdidos no
roundtrip — aceitável em dev.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extensão pgcrypto (pgp_sym_encrypt/decrypt + gen_random_bytes).
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # 2. Colunas novas em problemas.
    op.add_column("problemas", sa.Column("autor_cifrado", sa.LargeBinary(), nullable=True))
    op.add_column("problemas", sa.Column("autor_lookup", sa.LargeBinary(), nullable=True))
    op.add_column(
        "problemas",
        sa.Column(
            "anonimo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index("ix_problemas_autor_lookup", "problemas", ["autor_lookup"])

    # 3. Remove índice e coluna antiga (não há policy RLS sobre autor_hmac;
    # a policy problemas_autor_read referenciava autor_id e já foi dropada em 0010).
    op.drop_index("ix_problemas_autor_hmac", table_name="problemas")
    op.drop_column("problemas", "autor_hmac")

    # 4. users.nome_publico — exibido no feed.
    op.add_column("users", sa.Column("nome_publico", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "nome_publico")
    op.add_column("problemas", sa.Column("autor_hmac", sa.LargeBinary(), nullable=True))
    op.create_index("ix_problemas_autor_hmac", "problemas", ["autor_hmac"])
    op.drop_index("ix_problemas_autor_lookup", table_name="problemas")
    op.drop_column("problemas", "anonimo")
    op.drop_column("problemas", "autor_lookup")
    op.drop_column("problemas", "autor_cifrado")
    # pgcrypto deliberadamente não é dropada — outras migrations podem depender.
