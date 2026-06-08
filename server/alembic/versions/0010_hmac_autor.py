"""hmac do autor em problemas

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-03

Substitui problemas.autor_id (UUID texto plano, FK para users.id) por
problemas.autor_hmac (bytea, HMAC-SHA256 com chave secreta em env do backend).

Dump da tabela problemas — mesmo cruzando com users — deixa de ser suficiente
pra identificar autores sem AUTOR_HMAC_KEY.

ATENÇÃO no downgrade: recria autor_id VAZIO. HMAC é one-way; dados originais
ficam perdidos. Sem produção, isso é aceitável.

Detalhes de implementação:
- A migration 0001 criou o índice ix_problemas_autor_id; precisa ser dropado.
- A migration 0009 criou a policy RLS problemas_autor_read que referencia
  autor_id; precisa ser dropada antes de remover a coluna, e recriada no
  downgrade (apontando pro autor_id novamente vazio).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Nova coluna + índice.
    op.add_column("problemas", sa.Column("autor_hmac", sa.LargeBinary(), nullable=True))
    op.create_index("ix_problemas_autor_hmac", "problemas", ["autor_hmac"])

    # 2. Remove a policy RLS que referencia autor_id (criada em 0009).
    op.execute("DROP POLICY IF EXISTS problemas_autor_read ON problemas")

    # 3. Drop do índice antigo + FK + coluna autor_id.
    op.drop_index("ix_problemas_autor_id", table_name="problemas")
    op.drop_constraint("problemas_autor_id_fkey", "problemas", type_="foreignkey")
    op.drop_column("problemas", "autor_id")


def downgrade() -> None:
    # ATENÇÃO: recria autor_id vazio. HMAC é one-way; o vínculo original
    # NÃO é recuperável. Em produção isso seria perda de dados; em dev é OK.
    op.add_column("problemas", sa.Column("autor_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "problemas_autor_id_fkey",
        "problemas",
        "users",
        ["autor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_problemas_autor_id", "problemas", ["autor_id"])

    # Recria a policy RLS removida no upgrade (consistente com o estado pós-0009).
    op.execute(
        "CREATE POLICY problemas_autor_read ON problemas "
        "FOR SELECT TO authenticated USING (autor_id = auth.uid())"
    )

    op.drop_index("ix_problemas_autor_hmac", table_name="problemas")
    op.drop_column("problemas", "autor_hmac")
