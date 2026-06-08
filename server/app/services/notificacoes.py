import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.eventos import OutboxPublisher, Prioridade, TipoEvento

logger = logging.getLogger(__name__)
settings = get_settings()


def _dump_evento(evento: Any) -> dict:
    payload = evento.model_dump(exclude_none=True)
    return {key: value for key, value in payload.items() if value != []}


def _prioridade_problema(payload: dict) -> Prioridade:
    severidade = payload.get("severidade")
    confianca = payload.get("confianca")
    if (
        severidade in {"alta", "critica"}
        and confianca is not None
        and confianca >= settings.confianca_minima_revisao
    ):
        return "alta"
    if payload.get("raio_metros") is not None or payload.get("tokens_fcm"):
        return "alta"
    return "media"


def _publicar(db: Session, tipo: TipoEvento, payload: dict, prioridade: Prioridade) -> dict:
    OutboxPublisher(db).publish(tipo, payload, prioridade=prioridade)
    db.commit()
    logger.info("Evento de notificacao registrado | tipo=%s prioridade=%s", tipo, prioridade)
    return {
        "status": "registrado_no_outbox",
        "tipo": tipo,
        "prioridade": prioridade,
    }


def service_problema_criado(db: Session, evento) -> dict:
    payload = _dump_evento(evento)
    return _publicar(db, "problema.criado", payload, _prioridade_problema(payload))


def service_problema_resolvido(db: Session, evento) -> dict:
    payload = _dump_evento(evento)
    payload["status"] = "resolvido"
    return _publicar(db, "problema.status_alterado", payload, "media")


def service_politico_atualizado(db: Session, evento) -> dict:
    payload = _dump_evento(evento)
    return _publicar(db, "politico.atualizado", payload, "media")


def service_notificar_regiao(db: Session, evento) -> dict:
    payload = _dump_evento(evento)
    return _publicar(db, "problema.criado", payload, _prioridade_problema(payload))
