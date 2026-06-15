"""Valida que 0012 cria publicacoes e amplia ck_outbox_tipo com publicacao.criada."""
from collections.abc import Generator

import pytest
from alembic.config import Config
from sqlalchemy import Engine, inspect, text

from alembic import command
from app.core.config import get_settings
from app.db.session import engine as app_engine


@pytest.fixture
def alembic_cfg() -> Config:
    cfg = Config("alembic.ini")
    # Mesmo escape de % que env.py faz — senhas geradas podem ter '%'.
    cfg.set_main_option(
        "sqlalchemy.url", get_settings().database_url.replace("%", "%%")
    )
    return cfg


@pytest.fixture
def engine() -> Engine:
    return app_engine


@pytest.fixture(autouse=True)
def _restaurar_head(alembic_cfg: Config) -> Generator[None, None, None]:
    """Restaura DB ao head após cada teste destrutivo deste arquivo."""
    yield
    command.upgrade(alembic_cfg, "head")


def test_0012_cria_publicacoes(alembic_cfg: Config, engine: Engine) -> None:
    command.upgrade(alembic_cfg, "0012")
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("publicacoes")}
    assert {
        "id", "autor_cifrado", "autor_lookup", "anonimo",
        "conteudo", "imagem_url", "created_at",
    }.issubset(cols)
    idx = {i["name"] for i in insp.get_indexes("publicacoes")}
    assert "ix_publicacoes_autor_lookup" in idx
    assert "ix_publicacoes_created_at" in idx


def test_0012_amplia_outbox(alembic_cfg: Config, engine: Engine) -> None:
    command.upgrade(alembic_cfg, "0012")
    with engine.begin() as conn:
        # publicacao.criada deve ser aceito agora (id não tem default; geramos no INSERT)
        conn.execute(text(
            "INSERT INTO eventos_outbox (id, tipo, payload, prioridade) "
            "VALUES (gen_random_uuid(), 'publicacao.criada', '{}'::jsonb, 'baixa')"
        ))
        conn.execute(text("DELETE FROM eventos_outbox WHERE tipo = 'publicacao.criada'"))


def test_0012_downgrade(alembic_cfg: Config, engine: Engine) -> None:
    command.upgrade(alembic_cfg, "0012")
    command.downgrade(alembic_cfg, "0011")
    insp = inspect(engine)
    assert "publicacoes" not in insp.get_table_names()
