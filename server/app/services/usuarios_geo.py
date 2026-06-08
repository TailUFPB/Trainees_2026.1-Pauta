from dataclasses import dataclass
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.models.inscricao import Inscricao, SeguidorPolitico
from app.models.user import User

RAIOS_PADRAO_METROS = {
    "buraco": 500,
    "alagamento": 2000,
    "entulho": 800,
    "obstrucao_vegetacao": 800,
    "sinalizacao_defeituosa": 800,
    "iluminacao": 800,
    "calcada_irregular": 800,
    "outro": 500,
}


@dataclass(frozen=True)
class DestinatarioNotificacao:
    user_id: UUID
    email: str | None
    token_fcm: str | None
    distancia_metros: int | None = None


def raio_para_tipo(tipo_problema: str | None) -> int:
    return RAIOS_PADRAO_METROS.get(tipo_problema or "outro", RAIOS_PADRAO_METROS["outro"])


def _token_fcm_expr():
    return User.prefs_notificacao.op("->>")("token_fcm")


def _dedupe_com_canal(destinatarios: list[DestinatarioNotificacao]) -> list[DestinatarioNotificacao]:
    vistos: set[UUID] = set()
    resultado: list[DestinatarioNotificacao] = []
    for destinatario in destinatarios:
        if destinatario.user_id in vistos:
            continue
        if not destinatario.email and not destinatario.token_fcm:
            continue
        vistos.add(destinatario.user_id)
        resultado.append(destinatario)
    return resultado


def buscar_usuarios_por_raio(
    db: Session,
    *,
    lat: float,
    lng: float,
    raio_metros: int,
) -> list[DestinatarioNotificacao]:
    ponto = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    localizacao_geog = cast(User.localizacao, Geography(geometry_type="POINT", srid=4326))
    ponto_geog = cast(ponto, Geography(geometry_type="POINT", srid=4326))
    distancia = func.ST_Distance(localizacao_geog, ponto_geog)
    token_fcm = _token_fcm_expr().label("token_fcm")

    rows = db.execute(
        select(User.id, User.email, token_fcm, distancia.label("distancia_metros"))
        .where(User.localizacao.is_not(None))
        .where(func.ST_DWithin(localizacao_geog, ponto_geog, raio_metros))
        .order_by(distancia.asc())
    ).all()

    return _dedupe_com_canal(
        [
            DestinatarioNotificacao(
                user_id=user_id,
                email=email,
                token_fcm=token_fcm,
                distancia_metros=round(distancia_metros) if distancia_metros is not None else None,
            )
            for user_id, email, token_fcm, distancia_metros in rows
        ]
    )


def buscar_destinatarios_por_problema(
    db: Session, *, problema_id: UUID
) -> list[DestinatarioNotificacao]:
    token_fcm = _token_fcm_expr().label("token_fcm")
    rows = db.execute(
        select(User.id, User.email, token_fcm)
        .join(Inscricao, Inscricao.user_id == User.id)
        .where(Inscricao.problema_id == problema_id)
    ).all()
    return _dedupe_com_canal(
        [
            DestinatarioNotificacao(user_id=user_id, email=email, token_fcm=token_fcm)
            for user_id, email, token_fcm in rows
        ]
    )


def buscar_destinatarios_por_politico(
    db: Session, *, politico_id: UUID
) -> list[DestinatarioNotificacao]:
    token_fcm = _token_fcm_expr().label("token_fcm")
    rows = db.execute(
        select(User.id, User.email, token_fcm)
        .join(SeguidorPolitico, SeguidorPolitico.user_id == User.id)
        .where(SeguidorPolitico.politico_id == politico_id)
    ).all()
    return _dedupe_com_canal(
        [
            DestinatarioNotificacao(user_id=user_id, email=email, token_fcm=token_fcm)
            for user_id, email, token_fcm in rows
        ]
    )
