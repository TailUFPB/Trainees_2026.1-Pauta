"""Smoke do schema: problemas perdeu autor_id e ganhou autor_hmac."""

from sqlalchemy import inspect

from app.db.session import engine


def test_problemas_sem_autor_id():
    insp = inspect(engine)
    colunas = {c["name"] for c in insp.get_columns("problemas")}
    assert "autor_id" not in colunas, f"coluna autor_id deveria ter sido removida; presentes: {colunas}"


def test_problemas_com_autor_hmac():
    insp = inspect(engine)
    colunas = {c["name"] for c in insp.get_columns("problemas")}
    assert "autor_hmac" in colunas, f"coluna autor_hmac ausente; presentes: {colunas}"


def test_problemas_autor_hmac_indexado():
    insp = inspect(engine)
    indices = {ix["name"] for ix in insp.get_indexes("problemas")}
    assert "ix_problemas_autor_hmac" in indices, f"índice ausente; presentes: {indices}"
