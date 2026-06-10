import io
from datetime import UTC, datetime
from typing import BinaryIO
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_X, ST_Y, ST_MakeEnvelope
from jose import jwt as _jose_jwt
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import bearer, get_current_user
from app.core.config import get_settings
from app.core.hmac_autor import autor_hmac
from app.db.session import get_db
from app.models.inscricao import Inscricao
from app.models.problema import Problema
from app.models.user import User
from app.schemas.problema import (
    AtualizarStatusIn,
    ProblemaOut,
    ProblemaPublicoOut,
    Severidade,
)
from app.services import eventos, storage, visao
from app.services.eventos import Prioridade

router = APIRouter(prefix="/problemas", tags=["problemas"])
settings = get_settings()

_CONTENT_TYPES_OK = {"image/jpeg", "image/png", "image/webp"}
_CHUNK_BYTES = 64 * 1024

# Transições que o autor pode realizar no próprio reporte. Demais transições
# (em_andamento, arquivado, etc.) ficam fora desta fatia até existir RBAC.
_TRANSICOES_AUTOR_PERMITIDAS: set[tuple[str, str]] = {
    ("aberto", "cancelado"),
    ("aberto", "resolvido"),
    ("em_andamento", "resolvido"),
}


def _ler_upload_limitado(file: BinaryIO, max_bytes: int) -> bytes:
    """Lê o upload em chunks abortando com 413 antes de carregar mais que max_bytes na RAM."""
    buffer = bytearray()
    while True:
        chunk = file.read(_CHUNK_BYTES)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"Imagem maior que {max_bytes // (1024 * 1024)} MB.",
            )
    return bytes(buffer)


def _validar_imagem(conteudo: bytes, content_type: str) -> None:
    if content_type not in _CONTENT_TYPES_OK:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Formato não suportado: {content_type}. Use JPEG, PNG ou WEBP.",
        )
    if len(conteudo) > settings.max_upload_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Imagem maior que {settings.max_upload_bytes // (1024 * 1024)} MB.",
        )
    try:
        with Image.open(io.BytesIO(conteudo)) as img_verify:
            img_verify.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Imagem inválida.") from exc
    # PIL exige reabrir o arquivo após verify() para acessar size/pixels (estado indefinido).
    with Image.open(io.BytesIO(conteudo)) as img:
        largura, altura = img.size
    if min(largura, altura) < settings.resolucao_minima_px:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Resolução mínima é {settings.resolucao_minima_px}px no menor lado.",
        )


def _prioridade(severidade: Severidade, confianca: float) -> Prioridade:
    """Severidade alta/crítica com confiança suficiente vira notificação prioritária."""
    if severidade in ("alta", "critica") and confianca >= settings.confianca_minima_revisao:
        return "alta"
    if severidade == "media":
        return "media"
    return "baixa"


def _to_out(p: Problema, lat: float, lng: float) -> ProblemaOut:
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
        created_at=p.created_at,
    )


def _to_publico(p: Problema, lat: float, lng: float) -> ProblemaPublicoOut:
    """Projeção pública: oculta `autor_id` e `descricao` livre (potencial PII)."""
    return ProblemaPublicoOut(
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
        created_at=p.created_at,
    )


@router.post("", response_model=ProblemaOut, status_code=status.HTTP_201_CREATED)
def criar_problema(
    foto: UploadFile = File(...),
    lat: float = Form(..., ge=-90, le=90),
    lng: float = Form(..., ge=-180, le=180),
    descricao: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProblemaOut:
    """Reporta um problema: valida a foto, classifica via LLM (stub), grava com
    geometria PostGIS e produz o evento `problema.criado` no outbox."""
    conteudo = _ler_upload_limitado(foto.file, settings.max_upload_bytes)
    _validar_imagem(conteudo, foto.content_type or "")

    foto_url = storage.salvar_foto(conteudo, foto.content_type or "image/jpeg")
    classificacao = visao.classificar(conteudo)

    problema = Problema(
        autor_hmac=autor_hmac(user.id),
        foto_url=foto_url,
        localizacao=WKTElement(f"POINT({lng} {lat})", srid=4326),
        tipo_problema=classificacao.tipo_problema,
        severidade=classificacao.severidade,
        resumo_llm=classificacao.resumo_llm,
        palavras_chave=classificacao.palavras_chave,
        confianca=classificacao.confianca,
        modelo_utilizado=classificacao.modelo_utilizado,
        precisa_revisao=classificacao.confianca < settings.confianca_minima_revisao,
        descricao=descricao,
    )
    db.add(problema)
    db.flush()  # garante o id antes de montar o payload do evento

    eventos.OutboxPublisher(db).publish(
        "problema.criado",
        {
            "problema_id": str(problema.id),
            "tipo": classificacao.tipo_problema,
            "severidade": classificacao.severidade,
            "confianca": classificacao.confianca,
            "imagem_url": foto_url,
            "lat": lat,
            "lng": lng,
        },
        prioridade=_prioridade(classificacao.severidade, classificacao.confianca),
    )
    db.commit()
    db.refresh(problema)
    return _to_out(problema, lat, lng)


@router.post("/{problema_id}/inscrever", status_code=status.HTTP_204_NO_CONTENT)
def inscrever(
    problema_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Usuário/solvedor passa a seguir um problema (recebe alertas de atualização)."""
    if db.get(Problema, problema_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Problema não encontrado.")
    db.add(Inscricao(user_id=user.id, problema_id=problema_id, tipo="problema"))
    db.commit()


@router.get("", response_model=list[ProblemaPublicoOut])
def listar_problemas(
    bbox: str | None = Query(
        None, description="minLng,minLat,maxLng,maxLat — filtro espacial para o mapa"
    ),
    tipo: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    limite: int = Query(200, le=1000),
    db: Session = Depends(get_db),
) -> list[ProblemaPublicoOut]:
    """Lista problemas para o mapa, com filtro espacial por bounding box (índice GIST).

    Resposta pública: `autor_id` e `descricao` ficam ocultos (ver ProblemaPublicoOut).
    """
    stmt = select(
        Problema, ST_Y(Problema.localizacao).label("lat"), ST_X(Problema.localizacao).label("lng")
    )
    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = (float(x) for x in bbox.split(","))
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "bbox deve ser 'minLng,minLat,maxLng,maxLat'.",
            ) from exc
        envelope = ST_MakeEnvelope(min_lng, min_lat, max_lng, max_lat, 4326)
        stmt = stmt.where(func.ST_Intersects(Problema.localizacao, envelope))
    if tipo:
        stmt = stmt.where(Problema.tipo_problema == tipo)
    if status_:
        stmt = stmt.where(Problema.status == status_)
    stmt = stmt.order_by(Problema.created_at.desc()).limit(limite)

    return [_to_publico(p, lat, lng) for p, lat, lng in db.execute(stmt).all()]


@router.get("/{problema_id}", response_model=ProblemaPublicoOut)
def obter_problema(problema_id: UUID, db: Session = Depends(get_db)) -> ProblemaPublicoOut:
    """Detalhe público de um problema. Sem autor_id, sem descricao.

    Autores que querem o detalhe completo do próprio reporte usam
    GET /usuarios/me/problemas/{id}.
    """
    row = db.execute(
        select(Problema, ST_Y(Problema.localizacao), ST_X(Problema.localizacao)).where(
            Problema.id == problema_id
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Problema não encontrado.")
    p, lat, lng = row
    return _to_publico(p, lat, lng)


@router.patch("/{problema_id}/status", response_model=ProblemaOut)
def atualizar_status(
    problema_id: UUID,
    dados: AtualizarStatusIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    credenciais: HTTPAuthorizationCredentials = Depends(bearer),
) -> ProblemaOut:
    """O autor pode cancelar ou marcar como resolvido o próprio reporte.

    Demais transições (em_andamento, arquivado, etc.) são operacionais — ficam
    fora desta fatia até que role-based access esteja implementado.
    """
    row = db.execute(
        select(Problema, ST_Y(Problema.localizacao), ST_X(Problema.localizacao)).where(
            Problema.id == problema_id
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Problema não encontrado.")
    problema, lat, lng = row

    if problema.autor_hmac != autor_hmac(user.id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Só o autor pode mudar o status do próprio reporte.",
        )

    transicao = (problema.status, dados.status)
    if transicao not in _TRANSICOES_AUTOR_PERMITIDAS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Transição inválida pelo autor: {problema.status} → {dados.status}.",
        )

    problema.status = dados.status
    if dados.status == "resolvido":
        # Preenche resolvido_por com o email do JWT (autoautoria).
        # O token já foi validado por get_current_user; aqui só lemos um claim.
        email_autor = _jose_jwt.get_unverified_claims(credenciais.credentials).get("email")
        problema.resolvido_por = dados.resolvido_por or email_autor
        problema.resolvido_em = datetime.now(UTC)

    eventos.OutboxPublisher(db).publish(
        "problema.status_alterado",
        {
            "problema_id": str(problema.id),
            "status": dados.status,
            "resolvido_por": problema.resolvido_por,
        },
        prioridade="media",
    )
    db.commit()
    db.refresh(problema)
    return _to_out(problema, lat, lng)
