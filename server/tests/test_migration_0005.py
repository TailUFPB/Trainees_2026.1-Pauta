"""Índice cronológico complementar no outbox existe e está filtrado."""

from sqlalchemy import text


def test_indice_cronologico_outbox_existe(db):
    indexdef = db.execute(
        text(
            "SELECT indexdef FROM pg_indexes "
            "WHERE indexname = 'ix_eventos_outbox_pendentes_criado_em'"
        )
    ).scalar()
    assert indexdef is not None
    assert "criado_em" in indexdef
    assert "processado_em IS NULL" in indexdef


def test_indice_composite_pendentes_continua_existindo(db):
    """Regressão: o índice composite original não foi removido."""
    indexdef = db.execute(
        text(
            "SELECT indexdef FROM pg_indexes "
            "WHERE indexname = 'ix_eventos_outbox_pendentes'"
        )
    ).scalar()
    assert indexdef is not None
    assert "prioridade" in indexdef
