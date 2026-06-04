"""Documenta o invariante de escape de % em DATABASE_URL para o alembic ConfigParser."""

from configparser import ConfigParser


def test_set_main_option_aceita_percent_em_url():
    """O padrão usado em env.py: .replace('%', '%%') sobrevive ao round-trip do ConfigParser."""
    cp = ConfigParser()
    cp.add_section("alembic")
    url_com_percent = "postgresql+psycopg://pauta:p%ssword@db/pauta"

    cp.set("alembic", "sqlalchemy.url", url_com_percent.replace("%", "%%"))

    assert cp.get("alembic", "sqlalchemy.url") == url_com_percent


def test_url_sem_percent_nao_e_afetada():
    cp = ConfigParser()
    cp.add_section("alembic")
    url_normal = "postgresql+psycopg://pauta:senha@db/pauta"

    cp.set("alembic", "sqlalchemy.url", url_normal.replace("%", "%%"))

    assert cp.get("alembic", "sqlalchemy.url") == url_normal
