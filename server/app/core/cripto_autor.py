"""Cifra reversível do autor (pgcrypto) + lookup determinístico (HMAC).

Por que duas colunas?
- `autor_cifrado` (pgp_sym_encrypt, IV aleatório) é seguro mas não pesquisável.
- `autor_lookup` (HMAC determinístico) é pesquisável e serve pra autorização
  e pra consultar "minhas publicações" sem decifrar todas as linhas.
Chaves distintas (AUTOR_CIFRA_KEY ≠ AUTOR_LOOKUP_KEY) — vazamento de uma
não compromete a outra.
"""
import hashlib
import hmac as _hmac
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings


def cifrar_autor(db: Session, user_id: UUID) -> bytes:
    """pgp_sym_encrypt(user_id::text, AUTOR_CIFRA_KEY). Bytea opaco."""
    chave = get_settings().autor_cifra_key
    row = db.execute(
        text("SELECT pgp_sym_encrypt(:plain, :chave) AS c"),
        {"plain": str(user_id), "chave": chave},
    ).one()
    return bytes(row.c)


def decifrar_autor(db: Session, cifrado: bytes) -> UUID:
    """pgp_sym_decrypt(cifrado, AUTOR_CIFRA_KEY)::uuid."""
    chave = get_settings().autor_cifra_key
    row = db.execute(
        text("SELECT pgp_sym_decrypt(:cifrado, :chave) AS plain"),
        {"cifrado": cifrado, "chave": chave},
    ).one()
    return UUID(row.plain)


def lookup_autor(user_id: UUID, *, chave: bytes | None = None) -> bytes:
    """HMAC-SHA256(user_id, AUTOR_LOOKUP_KEY) — determinístico, indexado."""
    if chave is None:
        chave = get_settings().autor_lookup_key.encode()
    return _hmac.new(chave, str(user_id).encode(), hashlib.sha256).digest()


def payload_autor(
    db: Session, user_id: UUID, *, anonimo: bool
) -> tuple[bytes | None, bytes | None, bool]:
    """Triple usado ao inserir em `problemas`/`publicacoes`.

    Quando anônimo: cifrado e lookup ficam NULL — ninguém recupera identidade,
    nem mesmo o dono ou alguém com as chaves.
    """
    if anonimo:
        return (None, None, True)
    return (cifrar_autor(db, user_id), lookup_autor(user_id), False)
