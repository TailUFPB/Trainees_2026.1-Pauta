from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.recomendacao import PoliticoMatch, RecomendacaoOut
from app.services import recomendacao

router = APIRouter(prefix="/recomendacoes", tags=["recomendacoes"])


@router.get("", response_model=RecomendacaoOut)
def recomendar(
    limite: int = Query(10, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RecomendacaoOut:
    """Top políticos por similaridade de cosseno com os interesses do usuário.

    Estado placeholder enquanto o usuário não definir interesses ou enquanto o pipeline
    do colega não tiver populado os embeddings dos políticos.
    """
    if user.interesses_vetor is None:
        return RecomendacaoOut(placeholder=True)

    matches = recomendacao.top_politicos_por_similaridade(db, user.interesses_vetor, limite)
    if not matches:
        return RecomendacaoOut(placeholder=True)

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
        )
        for p, score in matches
    ]
    return RecomendacaoOut(
        placeholder=False,
        top_politicos=top,
        cluster_alinhado=recomendacao.cluster_alinhado(matches),
    )
