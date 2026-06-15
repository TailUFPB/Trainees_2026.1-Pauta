"""Smoke do schema: problemas perdeu autor_id, ganhou autor_cifrado + autor_lookup + anonimo."""

from sqlalchemy import inspect

from app.db.session import engine


def test_problemas_sem_autor_id():
    insp = inspect(engine)
    colunas = {c["name"] for c in insp.get_columns("problemas")}
    assert "autor_id" not in colunas, (
        f"coluna autor_id deveria ter sido removida; presentes: {colunas}"
    )


def test_problemas_com_autor_cifrado_e_lookup():
    insp = inspect(engine)
    colunas = {c["name"] for c in insp.get_columns("problemas")}
    for esperada in ("autor_cifrado", "autor_lookup", "anonimo"):
        assert esperada in colunas, (
            f"coluna {esperada} ausente; presentes: {colunas}"
        )


def test_problemas_autor_lookup_indexado():
    insp = inspect(engine)
    indices = {ix["name"] for ix in insp.get_indexes("problemas")}
    assert "ix_problemas_autor_lookup" in indices, (
        f"índice ix_problemas_autor_lookup ausente; presentes: {indices}"
    )
