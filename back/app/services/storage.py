"""Upload das fotos dos problemas.

Em produção sobe para o Supabase Storage (bucket configurável). Em dev, se o Supabase
não estiver configurado, grava em `./uploads` e serve via /uploads, para o fluxo rodar
end-to-end localmente sem depender do Supabase.
"""

from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings

settings = get_settings()
_UPLOAD_DIR = Path("uploads")


def _extensao(content_type: str) -> str:
    return {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(
        content_type, "bin"
    )


def salvar_foto(conteudo: bytes, content_type: str) -> str:
    """Salva a foto e devolve a URL pública. Usa Supabase Storage se configurado."""
    nome = f"{uuid4()}.{_extensao(content_type)}"

    if settings.supabase_url and settings.supabase_service_key:
        from supabase import create_client

        client = create_client(settings.supabase_url, settings.supabase_service_key)
        bucket = settings.supabase_storage_bucket
        client.storage.from_(bucket).upload(
            nome, conteudo, {"content-type": content_type}
        )
        return client.storage.from_(bucket).get_public_url(nome)

    # Fallback de desenvolvimento.
    _UPLOAD_DIR.mkdir(exist_ok=True)
    (_UPLOAD_DIR / nome).write_bytes(conteudo)
    return f"/uploads/{nome}"
