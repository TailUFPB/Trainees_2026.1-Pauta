"""rls e view problemas_publica

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-03

Habilita Row Level Security nas tabelas sensíveis e cria a view
`problemas_publica` que omite autor_id e descricao — ela é o ponto de leitura
público via PostgREST do Supabase quando algum cliente abusar do anon_key.

O backend FastAPI continua acessando as tabelas diretamente via SQLAlchemy
com role superuser (BYPASSRLS implícito). RLS aqui é defesa em profundidade
contra acesso via PostgREST.

No DB local (Docker), `auth.uid()` não existe; criamos um stub que retorna
NULL::uuid. Em produção (Supabase), a função real sobrescreve esse stub.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No Supabase, auth.uid() já existe. No DB local (Docker), criamos um stub
    # que retorna NULL — policies que dependem dele simplesmente filtram tudo,
    # o que é seguro (e o backend bypassa RLS de qualquer jeito).
    op.execute("""
        CREATE SCHEMA IF NOT EXISTS auth;
        CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid
            LANGUAGE sql STABLE AS $$ SELECT NULL::uuid $$;
    """)

    # 1. View pública sem PII
    op.execute("""
        CREATE OR REPLACE VIEW problemas_publica
        WITH (security_invoker = true) AS
        SELECT
            id, foto_url,
            ST_Y(localizacao) AS lat,
            ST_X(localizacao) AS lng,
            tipo_problema, severidade, resumo_llm, palavras_chave,
            confianca, modelo_utilizado, precisa_revisao,
            status, resolvido_por, resolvido_em, created_at
        FROM problemas
    """)
    # GRANTs pra roles do PostgREST (Supabase usa estes papéis padrão).
    # No DB local pode falhar se os roles não existem — wrap em DO block defensivo.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                EXECUTE 'GRANT SELECT ON problemas_publica TO anon';
            END IF;
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                EXECUTE 'GRANT SELECT ON problemas_publica TO authenticated';
            END IF;
        END $$;
    """)

    # 2. Habilitar RLS nas tabelas (idempotente — 0001 já habilitou,
    # mas reafirmamos pra que essa migration sozinha documente o estado final).
    for tabela in ("users", "problemas", "inscricoes", "seguidores_politico", "eventos_outbox", "politicos"):
        op.execute(f"ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY")

    # 3. Policies — todas referenciam auth.uid()
    # Mesma defensividade pra roles que podem não existir localmente.
    # CREATE POLICY ... TO <role> falha se role não existe. Garante criação.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                CREATE ROLE authenticated NOLOGIN;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                CREATE ROLE anon NOLOGIN;
            END IF;
        END $$;
    """)

    op.execute("CREATE POLICY users_self_read ON users FOR SELECT TO authenticated USING (id = auth.uid())")
    op.execute("CREATE POLICY users_self_update ON users FOR UPDATE TO authenticated USING (id = auth.uid())")
    op.execute("CREATE POLICY problemas_autor_read ON problemas FOR SELECT TO authenticated USING (autor_id = auth.uid())")
    op.execute("CREATE POLICY inscricoes_self ON inscricoes FOR ALL TO authenticated USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())")
    op.execute("CREATE POLICY seguidores_self ON seguidores_politico FOR ALL TO authenticated USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())")
    # eventos_outbox: deny all via PostgREST (sem policy = sem acesso quando RLS está habilitado)
    op.execute("CREATE POLICY politicos_read_public ON politicos FOR SELECT TO anon, authenticated USING (true)")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS politicos_read_public ON politicos")
    op.execute("DROP POLICY IF EXISTS seguidores_self ON seguidores_politico")
    op.execute("DROP POLICY IF EXISTS inscricoes_self ON inscricoes")
    op.execute("DROP POLICY IF EXISTS problemas_autor_read ON problemas")
    op.execute("DROP POLICY IF EXISTS users_self_update ON users")
    op.execute("DROP POLICY IF EXISTS users_self_read ON users")
    # NÃO desabilitamos RLS no downgrade — ela já estava habilitada desde 0001.
    op.execute("DROP VIEW IF EXISTS problemas_publica")
    # NÃO drope o schema auth nem a função uid — pode ser usado por outras coisas em prod.
