"""Comportamento das FKs em users após migration 0003.

Nota: o teste de ON DELETE SET NULL para problemas.autor_id foi removido — a
migration 0010 dropou a coluna autor_id e a FK; a autoria virou autor_hmac
(HMAC one-way), portanto a anonimização não depende mais de cascade.
"""

import uuid

from sqlalchemy import text


def test_delete_user_remove_inscricoes_e_seguidores(db):
    user_id = uuid.uuid4()
    politico_id = uuid.uuid4()

    db.execute(
        text("INSERT INTO users (id) VALUES (:id)"),
        {"id": user_id},
    )
    db.execute(
        text(
            "INSERT INTO politicos (id, nome, municipio) "
            "VALUES (:id, 'P', 'X')"
        ),
        {"id": politico_id},
    )
    db.execute(
        text(
            "INSERT INTO inscricoes (id, user_id, tipo, regiao) "
            "VALUES (:id, :uid, 'regiao', "
            "ST_GeomFromText('POLYGON((-38 -8,-38 -6,-36 -6,-36 -8,-38 -8))', 4326))"
        ),
        {"id": uuid.uuid4(), "uid": user_id},
    )
    db.execute(
        text(
            "INSERT INTO seguidores_politico (id, user_id, politico_id) "
            "VALUES (:id, :uid, :pid)"
        ),
        {"id": uuid.uuid4(), "uid": user_id, "pid": politico_id},
    )
    db.commit()

    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
    db.commit()

    inscricoes = db.execute(
        text("SELECT COUNT(*) FROM inscricoes WHERE user_id = :id"),
        {"id": user_id},
    ).scalar()
    seguidores = db.execute(
        text("SELECT COUNT(*) FROM seguidores_politico WHERE user_id = :id"),
        {"id": user_id},
    ).scalar()

    assert inscricoes == 0
    assert seguidores == 0
