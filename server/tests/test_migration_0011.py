"""Valida que 0011 instala pgcrypto, refatora problemas e adiciona nome_publico.

Diferente dos testes 0005-0007 (que checam estado pós-head), aqui exercitamos
o ciclo upgrade/downgrade explicitamente — porque 0011 é destrutivo (drop de
coluna) e o downgrade reintroduz `autor_hmac` vazio. Garantimos que o ciclo
fecha e que o estado final volta a `head` pra não contaminar outros testes.
"""
from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect, text

from app.core.config import get_settings
from app.db.session import engine as app_engine


@pytest.fixture
def alembic_cfg() -> Config:
    cfg = Config("alembic.ini")
    # Mesmo escape de % que env.py faz — senhas geradas (ex.: Supabase) podem ter '%'.
    cfg.set_main_option(
        "sqlalchemy.url", get_settings().database_url.replace("%", "%%")
    )
    return cfg


@pytest.fixture
def engine() -> Engine:
    return app_engine


@pytest.fixture(autouse=True)
def _restaurar_head(alembic_cfg: Config) -> Generator[None, None, None]:
    """Garante que após cada teste o DB volta a `head` — evita contaminar outros testes."""
    yield
    command.upgrade(alembic_cfg, "head")


def test_0011_upgrade(alembic_cfg: Config, engine: Engine) -> None:
    command.upgrade(alembic_cfg, "0011")

    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("problemas")}
    assert "autor_hmac" not in cols, "autor_hmac deve sair em 0011"
    assert "autor_cifrado" in cols
    assert "autor_lookup" in cols
    assert "anonimo" in cols
    user_cols = {c["name"] for c in insp.get_columns("users")}
    assert "nome_publico" in user_cols

    indexes = {i["name"] for i in insp.get_indexes("problemas")}
    assert "ix_problemas_autor_lookup" in indexes
    assert "ix_problemas_autor_hmac" not in indexes

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'")
        ).first()
        assert row is not None


def test_0011_downgrade(alembic_cfg: Config, engine: Engine) -> None:
    command.upgrade(alembic_cfg, "0011")
    command.downgrade(alembic_cfg, "0010")
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("problemas")}
    assert "autor_hmac" in cols
    assert "autor_cifrado" not in cols
