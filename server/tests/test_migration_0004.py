"""ux_politicos_municipio_nome com NULLS NOT DISTINCT bloqueia duplicatas com NULL."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_unique_municipio_nome_trata_null_como_igual(db):
    db.execute(
        text(
            "INSERT INTO politicos (id, nome, municipio) "
            "VALUES (:id, 'Maria', NULL)"
        ),
        {"id": uuid.uuid4()},
    )
    db.commit()

    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO politicos (id, nome, municipio) "
                "VALUES (:id, 'Maria', NULL)"
            ),
            {"id": uuid.uuid4()},
        )
        db.commit()


def test_indice_existe_com_nulls_not_distinct(db):
    indexdef = db.execute(
        text(
            "SELECT indexdef FROM pg_indexes "
            "WHERE indexname = 'ux_politicos_municipio_nome'"
        )
    ).scalar()
    assert indexdef is not None
    assert "NULLS NOT DISTINCT" in indexdef.upper()
