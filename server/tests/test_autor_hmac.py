"""HMAC determinístico do user_id pra pseudonimizar autoria de reportes."""

import uuid

from app.core.hmac_autor import autor_hmac


def test_hmac_deterministico_mesmo_user_mesma_chave():
    uid = uuid.uuid4()
    chave = b"test-key-32-bytes-minimum-aqui--"
    h1 = autor_hmac(uid, chave=chave)
    h2 = autor_hmac(uid, chave=chave)
    assert h1 == h2
    assert len(h1) == 32  # SHA256


def test_hmac_users_diferentes_geram_hashes_diferentes():
    chave = b"test-key-32-bytes-minimum-aqui--"
    h1 = autor_hmac(uuid.uuid4(), chave=chave)
    h2 = autor_hmac(uuid.uuid4(), chave=chave)
    assert h1 != h2


def test_hmac_muda_quando_chave_muda():
    uid = uuid.uuid4()
    h1 = autor_hmac(uid, chave=b"chave-original-32-bytes-minimum.")
    h2 = autor_hmac(uid, chave=b"chave-rotacionada-32-bytes-min..")
    assert h1 != h2
