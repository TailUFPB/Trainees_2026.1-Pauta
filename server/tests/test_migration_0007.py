"""ck_outbox_tipo aceita novos tipos de evento."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def _insert(db, tipo: str) -> None:
    db.execute(
        text(
            "INSERT INTO eventos_outbox (id, tipo, prioridade, payload) "
            "VALUES (:id, :t, 'media', '{}'::jsonb)"
        ),
        {"id": uuid.uuid4(), "t": tipo},
    )
    db.commit()


def test_tipo_politico_atualizado_aceito(db):
    _insert(db, "politico.atualizado")


def test_tipo_usuario_atualizado_aceito(db):
    _insert(db, "usuario.atualizado")


def test_tipos_originais_continuam_validos(db):
    _insert(db, "problema.criado")
    _insert(db, "problema.status_alterado")
    _insert(db, "politico.status_alterado")


def test_tipo_invalido_rejeitado(db):
    with pytest.raises(IntegrityError):
        _insert(db, "foo.bar")
