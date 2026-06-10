from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.notificacoes import (
    service_notificacao_teste,
    service_notificar_regiao,
    service_politico_atualizado,
    service_problema_criado,
    service_problema_resolvido,
)

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])

Severidade = Literal["baixa", "media", "alta", "critica"]


class EventoProblemaNotificacao(BaseModel):
    problema_id: str
    tipo: str
    rua: str | None = None
    distancia_metros: int | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    raio_metros: int | None = Field(default=None, gt=0)
    severidade: Severidade | None = None
    confianca: float | None = Field(default=None, ge=0, le=1)
    token_fcm: str | None = None
    email: str | None = None
    tokens_fcm: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)


class EventoProblemaResolvido(BaseModel):
    problema_id: str
    rua: str | None = None
    tipo: str | None = None
    responsavel: str | None = None
    token_fcm: str | None = None
    email: str | None = None
    tokens_fcm: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)


class EventoPoliticoAtualizado(BaseModel):
    politico_id: str
    nome_politico: str
    tipo_atualizacao: str
    descricao: str
    token_fcm: str | None = None
    email: str | None = None
    tokens_fcm: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)


class EventoNotificarRegiao(BaseModel):
    problema_id: str
    tipo: str
    rua: str | None = None
    distancia_metros: int | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    raio_metros: int | None = Field(default=None, gt=0)
    tokens_fcm: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)


class EventoTesteNotificacao(BaseModel):
    titulo: str = Field("Notificacao de teste", min_length=1, max_length=160)
    mensagem: str = Field(
        "Sua central interna de notificacoes esta funcionando.",
        min_length=1,
        max_length=4000,
    )


def _tem_destinatario_explicito(evento: BaseModel) -> bool:
    return bool(
        getattr(evento, "token_fcm", None)
        or getattr(evento, "email", None)
        or getattr(evento, "tokens_fcm", [])
        or getattr(evento, "emails", [])
    )


def _tem_geo(evento: BaseModel) -> bool:
    return getattr(evento, "lat", None) is not None and getattr(evento, "lng", None) is not None


def _exigir_destino_para_geoalerta(evento: BaseModel) -> None:
    if _tem_destinatario_explicito(evento) or _tem_geo(evento):
        return
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Informe lat/lng para busca geografica ou destinatarios explicitos.",
    )


@router.post("/problema-criado", status_code=status.HTTP_202_ACCEPTED)
def problema_criado(
    evento: EventoProblemaNotificacao,
    db: Session = Depends(get_db),
) -> dict:
    _exigir_destino_para_geoalerta(evento)
    return service_problema_criado(db, evento)


@router.post("/problema-resolvido", status_code=status.HTTP_202_ACCEPTED)
def problema_resolvido(
    evento: EventoProblemaResolvido,
    db: Session = Depends(get_db),
) -> dict:
    return service_problema_resolvido(db, evento)


@router.post("/politico-atualizado", status_code=status.HTTP_202_ACCEPTED)
def politico_atualizado(
    evento: EventoPoliticoAtualizado,
    db: Session = Depends(get_db),
) -> dict:
    return service_politico_atualizado(db, evento)


@router.post("/notificar-regiao", status_code=status.HTTP_202_ACCEPTED)
def notificar_regiao(
    evento: EventoNotificarRegiao,
    db: Session = Depends(get_db),
) -> dict:
    _exigir_destino_para_geoalerta(evento)
    return service_notificar_regiao(db, evento)


@router.post("/teste", status_code=status.HTTP_202_ACCEPTED)
def notificacao_teste(
    evento: EventoTesteNotificacao,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return service_notificacao_teste(
        db,
        user_id=str(user.id),
        titulo=evento.titulo,
        mensagem=evento.mensagem,
    )
