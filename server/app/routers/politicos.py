from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.inscricao import SeguidorPolitico
from app.models.politico import Politico
from app.models.user import User

router = APIRouter(prefix="/politicos", tags=["politicos"])


class PoliticoOut(BaseModel):
    id: UUID
    nome: str
    cargo: str | None
    partido: str | None
    municipio: str | None
    foto_url: str | None
    url_perfil: str | None
    cluster_id: int | None


@router.get("", response_model=list[PoliticoOut])
def listar_politicos(
    limite: int = 200, db: Session = Depends(get_db)
) -> list[PoliticoOut]:
    politicos = db.scalars(select(Politico).limit(limite)).all()
    return [
        PoliticoOut(
            id=p.id,
            nome=p.nome,
            cargo=p.cargo,
            partido=p.partido,
            municipio=p.municipio,
            foto_url=p.foto_url,
            url_perfil=p.fonte_url,
            cluster_id=p.cluster_id,
        )
        for p in politicos
    ]


@router.post("/{politico_id}/seguir", status_code=status.HTTP_204_NO_CONTENT)
def seguir(
    politico_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    if db.get(Politico, politico_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Político não encontrado.")
    db.add(SeguidorPolitico(user_id=user.id, politico_id=politico_id))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
        if constraint == "uq_seguidor_politico":
            return  # já segue — idempotente
        if constraint.endswith("_politico_id_fkey") or constraint.endswith("_user_id_fkey"):
            # Race: político (ou usuário) removido entre o guard e o commit.
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Recurso referenciado não existe."
            ) from exc
        raise
