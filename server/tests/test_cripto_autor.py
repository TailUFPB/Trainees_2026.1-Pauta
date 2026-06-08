"""Testa cifra reversível do autor + lookup HMAC."""
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.cripto_autor import (
    cifrar_autor,
    decifrar_autor,
    lookup_autor,
    payload_autor,
)


def test_cifrar_decifrar_roundtrip(db: Session) -> None:
    """cifrar(uid) → decifrar = uid original (via pgcrypto)."""
    uid = uuid4()
    cifrado = cifrar_autor(db, uid)
    assert isinstance(cifrado, bytes)
    assert len(cifrado) > 32  # pgp envelope é maior que o plaintext
    recuperado = decifrar_autor(db, cifrado)
    assert recuperado == uid


def test_cifrar_mesmo_uid_gera_bytes_diferentes(db: Session) -> None:
    """IV aleatório do pgp_sym_encrypt: mesmo input → ciphertexts diferentes."""
    uid = uuid4()
    a = cifrar_autor(db, uid)
    b = cifrar_autor(db, uid)
    assert a != b
    assert decifrar_autor(db, a) == decifrar_autor(db, b) == uid


def test_lookup_eh_deterministico() -> None:
    """HMAC do user.id é estável: mesma uid → mesmos bytes."""
    uid = uuid4()
    a = lookup_autor(uid)
    b = lookup_autor(uid)
    assert a == b
    assert isinstance(a, bytes)
    assert len(a) == 32  # SHA-256


def test_lookup_diferente_por_usuario() -> None:
    assert lookup_autor(uuid4()) != lookup_autor(uuid4())


def test_payload_anonimo_zera_tudo(db: Session) -> None:
    cifrado, lookup, anonimo = payload_autor(db, uuid4(), anonimo=True)
    assert cifrado is None
    assert lookup is None
    assert anonimo is True


def test_payload_nao_anonimo_preenche(db: Session) -> None:
    uid = uuid4()
    cifrado, lookup, anonimo = payload_autor(db, uid, anonimo=False)
    assert cifrado is not None and lookup is not None
    assert anonimo is False
    assert decifrar_autor(db, cifrado) == uid
    assert lookup == lookup_autor(uid)
