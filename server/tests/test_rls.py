"""Smoke test: RLS está habilitado nas tabelas e view problemas_publica existe."""

from sqlalchemy import text

from app.db.session import engine

_TABELAS_COM_RLS = [
    "users",
    "problemas",
    "inscricoes",
    "seguidores_politico",
    "eventos_outbox",
    "notificacoes",
    "politicos",
]


def test_rls_habilitado_em_tabelas_sensiveis():
    with engine.connect() as conn:
        for t in _TABELAS_COM_RLS:
            row = conn.execute(
                text("SELECT relrowsecurity FROM pg_class WHERE relname = :t"),
                {"t": t},
            ).first()
            assert row is not None, f"tabela {t} não encontrada"
            assert row[0] is True, f"RLS não habilitado em {t}"


def test_view_problemas_publica_existe_sem_pii():
    with engine.connect() as conn:
        cols = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name='problemas_publica'"
                )
            ).all()
        }
        assert cols, "view problemas_publica não existe"
        assert "autor_id" not in cols
        assert "descricao" not in cols
        # Sanidade: campos públicos presentes
        assert {"id", "status", "tipo_problema", "severidade"} <= cols
