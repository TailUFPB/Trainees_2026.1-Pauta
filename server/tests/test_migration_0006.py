"""ck_problemas_status passa a aceitar 'arquivado' e 'cancelado'."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def _insert(db, status: str) -> None:
    db.execute(
        text(
            "INSERT INTO problemas (id, localizacao, status) "
            "VALUES (:id, ST_GeomFromText('POINT(-37 -7)', 4326), :s)"
        ),
        {"id": uuid.uuid4(), "s": status},
    )
    db.commit()


def test_status_arquivado_aceito(db):
    _insert(db, "arquivado")


def test_status_cancelado_aceito(db):
    _insert(db, "cancelado")


def test_status_original_continua_valido(db):
    _insert(db, "aberto")


def test_status_invalido_rejeitado(db):
    with pytest.raises(IntegrityError):
        _insert(db, "lixo_aleatorio")
