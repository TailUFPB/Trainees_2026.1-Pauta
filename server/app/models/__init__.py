"""Importa todos os modelos para que o Alembic os descubra via Base.metadata."""

from app.models.evento import EventoOutbox
from app.models.inscricao import Inscricao, SeguidorPolitico
from app.models.notificacao import Notificacao
from app.models.politico import Politico
from app.models.problema import Problema
from app.models.user import User

__all__ = [
    "User",
    "Problema",
    "Politico",
    "Inscricao",
    "SeguidorPolitico",
    "EventoOutbox",
    "Notificacao",
]
