from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.recomendacao import (
    EvidenciaProposta,
    InteressesIn,
    PoliticoMatch,
    RecomendacaoOut,
)
from app.services import recomendacao

router = APIRouter(prefix="/recomendacoes", tags=["recomendacoes"])


def _montar_recomendacao(
    db: Session,
    user: User,
    limite: int,
    texto: str | None = None,
) -> RecomendacaoOut:
    if user.interesses_vetor is None:
        return RecomendacaoOut(placeholder=True)

    matches = recomendacao.top_politicos_por_similaridade(db, user.interesses_vetor, limite)
    if not matches:
        return RecomendacaoOut(placeholder=True)

    # evidências por político (semânticas)
    com_evidencias = [
        (p, score, recomendacao.evidencias_para_politico(user.interesses_vetor, p))
        for p, score in matches
    ]
    # justificativa sob medida via LLM (só quando há o texto da query, ex.: no POST):
    # 1 chamada batched p/ os que têm evidência; fallback pro texto-base se falhar/sem chave.
    just_llm = (
        recomendacao.justificativas_llm(texto, [(p, evs) for p, _, evs in com_evidencias if evs])
        if texto
        else {}
    )

    top = [
        PoliticoMatch(
            id=p.id,
            nome=p.nome,
            cargo=p.cargo,
            partido=p.partido,
            municipio=p.municipio,
            resumo_llm=p.resumo_llm,
            cluster_id=p.cluster_id,
            score=round(score, 4),
            justificativa=just_llm.get(p.id) or recomendacao.justificativa_para(p, evidencias),
            evidencias=[
                EvidenciaProposta(tipo=e.tipo, numero=e.numero, ano=e.ano, resumo=e.resumo)
                for e in evidencias
            ],
        )
        for p, score, evidencias in com_evidencias
    ]
    return RecomendacaoOut(
        placeholder=False,
        top_politicos=top,
        cluster_alinhado=recomendacao.cluster_alinhado(matches),
    )


@router.get("", response_model=RecomendacaoOut)
def recomendar(
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RecomendacaoOut:
    """Reapresenta recomendações usando o vetor de interesses salvo."""
    return _montar_recomendacao(db, user, limite)


@router.post("", response_model=RecomendacaoOut)
def gerar_recomendacoes(
    dados: InteressesIn,
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RecomendacaoOut:
    """Atualiza o vetor de interesses do cidadão e devolve o ranking + evidências."""
    user.interesses_vetor = recomendacao.gerar_embedding(dados.texto)
    db.add(user)
    db.commit()
    return _montar_recomendacao(db, user, limite, texto=dados.texto)
