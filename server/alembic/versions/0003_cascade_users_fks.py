"""cascade users fks

Revision ID: 0003_cascade_users_fks
Revises: 0002_politico_foto_url
Create Date: 2026-06-03

FKs em public.users com ON DELETE coerente:
- problemas.autor_id  -> SET NULL (preserva denúncia, anonimiza autor)
- inscricoes.user_id  -> CASCADE  (interesse sem dono não faz sentido)
- seguidores_politico.user_id -> CASCADE (idem)

Resolve a colisão com auth.users -> public.users ON DELETE CASCADE (definido em
0001), que bloqueava deleção de usuário no Supabase sempre que ele tinha rows
nessas tabelas dependentes (default NO ACTION).
"""

from alembic import op


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # problemas.autor_id -> users.id  ON DELETE SET NULL
    op.drop_constraint("problemas_autor_id_fkey", "problemas", type_="foreignkey")
    op.create_foreign_key(
        "problemas_autor_id_fkey",
        "problemas",
        "users",
        ["autor_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # inscricoes.user_id -> users.id  ON DELETE CASCADE
    op.drop_constraint("inscricoes_user_id_fkey", "inscricoes", type_="foreignkey")
    op.create_foreign_key(
        "inscricoes_user_id_fkey",
        "inscricoes",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # seguidores_politico.user_id -> users.id  ON DELETE CASCADE
    op.drop_constraint(
        "seguidores_politico_user_id_fkey", "seguidores_politico", type_="foreignkey"
    )
    op.create_foreign_key(
        "seguidores_politico_user_id_fkey",
        "seguidores_politico",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "seguidores_politico_user_id_fkey", "seguidores_politico", type_="foreignkey"
    )
    op.create_foreign_key(
        "seguidores_politico_user_id_fkey",
        "seguidores_politico",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("inscricoes_user_id_fkey", "inscricoes", type_="foreignkey")
    op.create_foreign_key(
        "inscricoes_user_id_fkey",
        "inscricoes",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("problemas_autor_id_fkey", "problemas", type_="foreignkey")
    op.create_foreign_key(
        "problemas_autor_id_fkey",
        "problemas",
        "users",
        ["autor_id"],
        ["id"],
    )
