from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_X, ST_Y
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.cripto_autor import lookup_autor
from app.db.session import get_db
from app.models.problema import Problema
from app.models.user import User
from app.schemas.problema import ProblemaOut, StatusProblema
from app.schemas.recomendacao import InteressesIn
from app.services import recomendacao
from app.services.notificacoes_internas import (
    contar_nao_lidas,
    listar_notificacoes,
    marcar_como_lida,
    normalizar_prefs_notificacao,
    salvar_prefs_notificacao,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def _to_problema_out(
    p: Problema, lat: float, lng: float, autor_nome: str | None
) -> ProblemaOut:
    return ProblemaOut(
        id=p.id,
        foto_url=p.foto_url,
        lat=lat,
        lng=lng,
        tipo_problema=p.tipo_problema,
        severidade=p.severidade,
        resumo_llm=p.resumo_llm,
        palavras_chave=p.palavras_chave,
        confianca=p.confianca,
        modelo_utilizado=p.modelo_utilizado,
        precisa_revisao=p.precisa_revisao,
        status=p.status,
        resolvido_por=p.resolvido_por,
        resolvido_em=p.resolvido_em,
        descricao=p.descricao,
        autor_nome=autor_nome,
        anonimo=p.anonimo,
        created_at=p.created_at,
    )


class LocalizacaoIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class UsuarioOut(BaseModel):
    id: str
    tem_interesses: bool
    tem_localizacao: bool


class NotificacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo: str
    titulo: str
    mensagem: str
    link_destino: str | None
    lida: bool
    canais: dict
    dados: dict
    created_at: datetime
    lida_em: datetime | None


class ContagemNotificacoesOut(BaseModel):
    nao_lidas: int


class PreferenciasNotificacaoIn(BaseModel):
    interna: bool | None = None
    email: bool | None = None
    push: bool | None = None
    problemas_perto: bool | None = None
    politicos: bool | None = None
    resumo_semanal: bool | None = None
    token_fcm: str | None = None


class PreferenciasNotificacaoOut(BaseModel):
    prefs_notificacao: dict


@router.get("/me", response_model=UsuarioOut)
def me(user: User = Depends(get_current_user)) -> UsuarioOut:
    return UsuarioOut(
        id=str(user.id),
        tem_interesses=user.interesses_vetor is not None,
        tem_localizacao=user.localizacao is not None,
    )


@router.post("/me/interesses", response_model=UsuarioOut)
def definir_interesses(
    dados: InteressesIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UsuarioOut:
    """Gera (stub) o embedding dos interesses do cidadão para a recomendação."""
    user.interesses_vetor = recomendacao.gerar_embedding(dados.texto)
    db.commit()
    db.refresh(user)
    return me(user)


@router.put("/me/localizacao", response_model=UsuarioOut)
def definir_localizacao(
    dados: LocalizacaoIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UsuarioOut:
    """Define a localização 'de casa' usada nos geo-alertas de proximidade."""
    user.localizacao = WKTElement(f"POINT({dados.lng} {dados.lat})", srid=4326)
    db.commit()
    db.refresh(user)
    return me(user)


@router.get("/me/problemas", response_model=list[ProblemaOut])
def listar_meus_problemas(
    status: Annotated[list[StatusProblema] | None, Query()] = None,
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProblemaOut]:
    """Lista os problemas reportados pelo usuário autenticado, com filtros."""
    stmt = (
        select(
            Problema,
            ST_Y(Problema.localizacao).label("lat"),
            ST_X(Problema.localizacao).label("lng"),
        )
        .where(Problema.autor_lookup == lookup_autor(user.id))
        .order_by(Problema.created_at.desc())
    )
    if status:
        stmt = stmt.where(Problema.status.in_(status))
    stmt = stmt.limit(limite).offset(offset)
    # Esta é a rota "meus reportes" — autor é sempre o usuário autenticado.
    # Anônimo continua None; do contrário, vem direto de user.nome_publico (sem decifrar).
    return [
        _to_problema_out(p, lat, lng, None if p.anonimo else user.nome_publico)
        for p, lat, lng in db.execute(stmt).all()
    ]


@router.get("/me/problemas/{problema_id}", response_model=ProblemaOut)
def obter_meu_problema(
    problema_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProblemaOut:
    """Detalhe completo de um reporte do próprio usuário autenticado.

    404 se o reporte não existe OU se quem chama não é o autor (sem distinção
    pra não vazar a existência do reporte).
    """
    row = db.execute(
        select(
            Problema,
            ST_Y(Problema.localizacao).label("lat"),
            ST_X(Problema.localizacao).label("lng"),
        ).where(
            Problema.id == problema_id,
            Problema.autor_lookup == lookup_autor(user.id),
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte não encontrado.")
    p, lat, lng = row
    autor_nome = None if p.anonimo else user.nome_publico
    return _to_problema_out(p, lat, lng, autor_nome)


@router.get("/me/notificacoes", response_model=list[NotificacaoOut])
def minhas_notificacoes(
    apenas_nao_lidas: bool = False,
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list:
    """Lista a central interna de notificacoes do usuario autenticado."""
    return listar_notificacoes(
        db,
        user_id=user.id,
        apenas_nao_lidas=apenas_nao_lidas,
        limite=limite,
        offset=offset,
    )


@router.get("/me/notificacoes/contagem", response_model=ContagemNotificacoesOut)
def contagem_notificacoes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContagemNotificacoesOut:
    return ContagemNotificacoesOut(nao_lidas=contar_nao_lidas(db, user_id=user.id))


@router.patch("/me/notificacoes/{notificacao_id}/lida", response_model=NotificacaoOut)
def marcar_notificacao_lida(
    notificacao_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notificacao = marcar_como_lida(db, user_id=user.id, notificacao_id=notificacao_id)
    if notificacao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificacao nao encontrada.")
    db.commit()
    db.refresh(notificacao)
    return notificacao


@router.get("/me/notificacoes/preferencias", response_model=PreferenciasNotificacaoOut)
def obter_preferencias_notificacao(user: User = Depends(get_current_user)):
    return PreferenciasNotificacaoOut(
        prefs_notificacao=normalizar_prefs_notificacao(user.prefs_notificacao)
    )


@router.patch("/me/notificacoes", response_model=PreferenciasNotificacaoOut)
def atualizar_preferencias_notificacao(
    dados: PreferenciasNotificacaoIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prefs = salvar_prefs_notificacao(user, dados.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(user)
    return PreferenciasNotificacaoOut(prefs_notificacao=prefs)
