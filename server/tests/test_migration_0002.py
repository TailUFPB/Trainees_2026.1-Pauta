from sqlalchemy import inspect

from app.db.session import engine


def test_foto_url_existe_na_tabela_politicos():
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("politicos")}
    assert "foto_url" in cols


def test_unique_index_municipio_nome():
    insp = inspect(engine)
    indices = {ix["name"]: ix for ix in insp.get_indexes("politicos")}
    assert "ux_politicos_municipio_nome" in indices
    assert indices["ux_politicos_municipio_nome"]["unique"] is True
    assert indices["ux_politicos_municipio_nome"]["column_names"] == ["municipio", "nome"]
