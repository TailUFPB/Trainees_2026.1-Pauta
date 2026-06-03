"""Comportamento das FKs em users após migration 0003."""

import uuid

from sqlalchemy import text


def test_delete_user_seta_autor_null_em_problemas(db):
    user_id = uuid.uuid4()
    problema_id = uuid.uuid4()

    db.execute(
        text("INSERT INTO users (id) VALUES (:id)"),
        {"id": user_id},
    )
    db.execute(
        text(
            "INSERT INTO problemas (id, autor_id, localizacao) "
            "VALUES (:pid, :aid, ST_GeomFromText('POINT(-37 -7)', 4326))"
        ),
        {"pid": problema_id, "aid": user_id},
    )
    db.commit()

    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
    db.commit()

    autor = db.execute(
        text("SELECT autor_id FROM problemas WHERE id = :id"), {"id": problema_id}
    ).scalar()
    # Problema sobrevive, autor é anonimizado.
    assert autor is None


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
