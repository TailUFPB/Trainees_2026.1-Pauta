from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.cripto_autor import lookup_autor, payload_autor
from app.db.session import get_db
from app.models.publicacao import Publicacao
from app.models.user import User
from app.schemas.publicacao import PublicacaoOut
from app.services import eventos, storage
from app.services.imagem import ler_upload_limitado, validar_imagem

router = APIRouter(tags=["publicacoes"])
settings = get_settings()

CONTEUDO_MAX = 1000


def _to_out(p: Publicacao, autor_nome: str | None) -> PublicacaoOut:
    return PublicacaoOut(
        id=p.id,
        conteudo=p.conteudo,
        imagem_url=p.imagem_url,
        anonimo=p.anonimo,
        autor_nome=autor_nome,
        created_at=p.created_at,
    )


@router.post("/publicacoes", response_model=PublicacaoOut, status_code=status.HTTP_201_CREATED)
def criar_publicacao(
    conteudo: str = Form(..., max_length=CONTEUDO_MAX),
    anonimo: bool = Form(False),
    foto: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PublicacaoOut:
    """Cria um post no feed. Aceita multipart com `foto` opcional (JPEG/PNG/WEBP);
    a imagem é validada e enviada ao storage, gravando a URL pública em `imagem_url`."""
    conteudo_limpo = conteudo.strip()
    if not conteudo_limpo:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "conteudo não pode ser só espaços em branco.",
        )

    imagem_url: str | None = None
    # UploadFile vazio (campo enviado sem arquivo) chega com filename ausente.
    if foto is not None and foto.filename:
        bytes_foto = ler_upload_limitado(foto.file, settings.max_upload_bytes)
        validar_imagem(bytes_foto, foto.content_type or "")
        imagem_url = storage.salvar_foto(bytes_foto, foto.content_type or "image/jpeg")

    cifrado, lookup, anonimo = payload_autor(db, user.id, anonimo=anonimo)
    pub = Publicacao(
        autor_cifrado=cifrado,
        autor_lookup=lookup,
        anonimo=anonimo,
        conteudo=conteudo_limpo,
        imagem_url=imagem_url,
    )
    db.add(pub)
    db.flush()
    eventos.OutboxPublisher(db).publish(
        "publicacao.criada",
        {"publicacao_id": str(pub.id), "anonimo": anonimo},
        prioridade="baixa",
    )
    db.commit()
    db.refresh(pub)
    autor_nome = None if anonimo else user.nome_publico
    return _to_out(pub, autor_nome)


@router.get("/usuarios/me/publicacoes", response_model=list[PublicacaoOut])
def listar_minhas_publicacoes(
    limite: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[PublicacaoOut]:
    """Apenas publicações NÃO-anônimas. Anônimas são intencionalmente irrecuperáveis
    (autor_lookup é NULL para elas)."""
    stmt = (
        select(Publicacao)
        .where(Publicacao.autor_lookup == lookup_autor(user.id))
        .order_by(Publicacao.created_at.desc())
        .limit(limite)
        .offset(offset)
    )
    return [_to_out(p, user.nome_publico) for p in db.execute(stmt).scalars().all()]
