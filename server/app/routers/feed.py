"""Timeline social unificada — publicacoes + problemas ordenados por created_at.

Para cada item exibe `autor_nome` resolvido via JOIN com `users.nome_publico`
após decifrar `autor_cifrado` em SQL (pgcrypto). Itens anônimos têm autor_nome=NULL.
"""
import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.feed import ItemFeed, ItemFeedProblema, ItemFeedPublicacao

router = APIRouter(prefix="/feed", tags=["feed"])
settings = get_settings()


@router.get("", response_model=list[ItemFeed])
def listar_feed(
    limite: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(
        None,
        description="ISO timestamp do último item visto (created_at). Paginação por cursor.",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),  # exige auth
) -> list[ItemFeed]:
    chave = settings.autor_cifra_key

    sql_pubs = sa.text("""
        SELECT id, conteudo, imagem_url, anonimo, created_at,
               CASE
                   WHEN anonimo OR autor_cifrado IS NULL THEN NULL
                   ELSE (SELECT nome_publico FROM users
                         WHERE id = pgp_sym_decrypt(autor_cifrado, :chave)::uuid)
               END AS autor_nome
        FROM publicacoes
        WHERE (CAST(:cursor AS timestamptz) IS NULL
               OR created_at < CAST(:cursor AS timestamptz))
        ORDER BY created_at DESC
        LIMIT :limite
    """)
    pubs = db.execute(
        sql_pubs, {"chave": chave, "cursor": cursor, "limite": limite}
    ).all()

    sql_probs = sa.text("""
        SELECT p.id, p.foto_url, ST_Y(p.localizacao) AS lat, ST_X(p.localizacao) AS lng,
               p.tipo_problema, p.severidade, p.resumo_llm, p.status,
               p.anonimo, p.created_at,
               CASE
                   WHEN p.anonimo OR p.autor_cifrado IS NULL THEN NULL
                   ELSE (SELECT nome_publico FROM users
                         WHERE id = pgp_sym_decrypt(p.autor_cifrado, :chave)::uuid)
               END AS autor_nome
        FROM problemas p
        WHERE (CAST(:cursor AS timestamptz) IS NULL
               OR p.created_at < CAST(:cursor AS timestamptz))
        ORDER BY p.created_at DESC
        LIMIT :limite
    """)
    probs = db.execute(
        sql_probs, {"chave": chave, "cursor": cursor, "limite": limite}
    ).all()

    itens: list[ItemFeed] = []
    for r in pubs:
        itens.append(
            ItemFeedPublicacao(
                id=r.id,
                conteudo=r.conteudo,
                imagem_url=r.imagem_url,
                anonimo=r.anonimo,
                autor_nome=r.autor_nome,
                created_at=r.created_at,
            )
        )
    for r in probs:
        itens.append(
            ItemFeedProblema(
                id=r.id,
                foto_url=r.foto_url,
                lat=r.lat,
                lng=r.lng,
                tipo_problema=r.tipo_problema,
                severidade=r.severidade,
                resumo_llm=r.resumo_llm,
                status=r.status,
                anonimo=r.anonimo,
                autor_nome=r.autor_nome,
                created_at=r.created_at,
            )
        )
    itens.sort(key=lambda x: x.created_at, reverse=True)
    return itens[:limite]
