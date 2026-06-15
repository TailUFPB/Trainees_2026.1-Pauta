from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.notificacao import Notificacao
from app.models.user import User

PREFS_NOTIFICACAO_PADRAO = {
    "interna": True,
    "email": True,
    "push": True,
    "problemas_perto": True,
    "politicos": True,
    "resumo_semanal": False,
}


def normalizar_prefs_notificacao(prefs: dict | None) -> dict:
    return {**PREFS_NOTIFICACAO_PADRAO, **(prefs or {})}


def canal_habilitado(prefs: dict | None, canal: str) -> bool:
    return bool(normalizar_prefs_notificacao(prefs).get(canal, True))


def salvar_prefs_notificacao(user: User, alteracoes: dict) -> dict:
    prefs = normalizar_prefs_notificacao(user.prefs_notificacao)
    prefs.update({chave: valor for chave, valor in alteracoes.items() if valor is not None})
    user.prefs_notificacao = prefs
    return prefs


def criar_notificacao(
    db: Session,
    *,
    user_id: UUID,
    origem_evento_id: UUID | None,
    tipo: str,
    titulo: str,
    mensagem: str,
    link_destino: str | None = None,
    canais: dict | None = None,
    dados: dict | None = None,
) -> bool:
    stmt = (
        insert(Notificacao)
        .values(
            origem_evento_id=origem_evento_id,
            user_id=user_id,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            link_destino=link_destino,
            canais=canais or {},
            dados=dados or {},
        )
        .on_conflict_do_nothing(constraint="uq_notificacoes_evento_usuario_tipo")
        .returning(Notificacao.id)
    )
    return db.scalar(stmt) is not None


def listar_notificacoes(
    db: Session,
    *,
    user_id: UUID,
    apenas_nao_lidas: bool = False,
    limite: int = 20,
    offset: int = 0,
) -> list[Notificacao]:
    stmt = select(Notificacao).where(Notificacao.user_id == user_id)
    if apenas_nao_lidas:
        stmt = stmt.where(Notificacao.lida.is_(False))
    stmt = stmt.order_by(Notificacao.created_at.desc()).limit(limite).offset(offset)
    return list(db.scalars(stmt).all())


def contar_nao_lidas(db: Session, *, user_id: UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Notificacao)
            .where(Notificacao.user_id == user_id, Notificacao.lida.is_(False))
        )
        or 0
    )


def marcar_como_lida(db: Session, *, user_id: UUID, notificacao_id: UUID) -> Notificacao | None:
    notificacao = db.get(Notificacao, notificacao_id)
    if notificacao is None or notificacao.user_id != user_id:
        return None
    if not notificacao.lida:
        notificacao.lida = True
        notificacao.lida_em = datetime.now(UTC)
    return notificacao
