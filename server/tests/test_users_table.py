"""Garantia de schema: users não pode mais ter nome/email após a migration 0008."""

from sqlalchemy import inspect

from app.db.session import engine


def test_users_sem_nome_nem_email():
    insp = inspect(engine)
    colunas = {c["name"] for c in insp.get_columns("users")}
    assert "nome" not in colunas, f"coluna 'nome' deveria ter sido removida; presentes: {colunas}"
    assert "email" not in colunas, f"coluna 'email' deveria ter sido removida; presentes: {colunas}"
    # Sanidade: colunas que devem permanecer.
    assert {"id", "localizacao", "interesses_vetor", "prefs_notificacao", "created_at"} <= colunas
