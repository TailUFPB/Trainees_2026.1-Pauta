from fastapi import APIRouter, Depends
from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.recomendacao import InteressesIn
from app.services import recomendacao

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


class LocalizacaoIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class UsuarioOut(BaseModel):
    id: str
    nome: str | None
    email: str | None
    tem_interesses: bool
    tem_localizacao: bool


@router.get("/me", response_model=UsuarioOut)
def me(user: User = Depends(get_current_user)) -> UsuarioOut:
    return UsuarioOut(
        id=str(user.id),
        nome=user.nome,
        email=user.email,
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
