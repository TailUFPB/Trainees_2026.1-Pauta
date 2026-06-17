"""Leitura e validação de uploads de imagem.

Compartilhado por `problemas` (foto do reporte) e `publicacoes` (foto do post),
para que as mesmas regras de tamanho, formato e resolução valham nos dois fluxos.
"""

import io
from typing import BinaryIO

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

settings = get_settings()

CONTENT_TYPES_OK = {"image/jpeg", "image/png", "image/webp"}
_CHUNK_BYTES = 64 * 1024


def ler_upload_limitado(file: BinaryIO, max_bytes: int) -> bytes:
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


def validar_imagem(conteudo: bytes, content_type: str) -> None:
    """Rejeita formato/tamanho/resolução inválidos (415/413/422) antes de persistir."""
    if content_type not in CONTENT_TYPES_OK:
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
