"""Regressão: migrations não podem sobrescrever auth.uid() do Supabase."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def test_migration_0009_preserva_auth_uid_nativa(monkeypatch) -> None:
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "0009_rls_e_view_publica.py"
    )
    spec = spec_from_file_location("migration_0009", migration_path)
    assert spec is not None and spec.loader is not None
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)

    statements: list[str] = []
    monkeypatch.setattr(migration.op, "execute", statements.append)

    migration.upgrade()

    auth_uid_sql = statements[0]
    assert "to_regprocedure('auth.uid()') IS NULL" in auth_uid_sql
    assert "CREATE FUNCTION auth.uid()" in auth_uid_sql
    assert "CREATE OR REPLACE FUNCTION auth.uid()" not in auth_uid_sql
