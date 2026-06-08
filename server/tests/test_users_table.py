"""Garantia de schema: users mantem somente o PII necessario para notificacoes."""

from sqlalchemy import inspect

from app.db.session import engine


def test_users_sem_nome_com_email_operacional():
    insp = inspect(engine)
    colunas = {c["name"] for c in insp.get_columns("users")}
    assert "nome" not in colunas, f"coluna 'nome' deveria ter sido removida; presentes: {colunas}"
    assert "email" in colunas, f"coluna 'email' deve existir para notificacoes; presentes: {colunas}"
    # Sanidade: colunas que devem permanecer.
    assert {"id", "localizacao", "interesses_vetor", "prefs_notificacao", "created_at"} <= colunas
