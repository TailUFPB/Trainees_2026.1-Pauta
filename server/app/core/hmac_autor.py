"""HMAC-SHA256 determinístico do user.id para pseudonimizar autoria de reportes.

A chave (AUTOR_HMAC_KEY) mora em env e é estável ao longo da vida do projeto.
Rotação exige re-HMAC de toda a tabela problemas — não fazer sem plano.
"""

import hashlib
import hmac as _hmac
from uuid import UUID

from app.core.config import get_settings


def autor_hmac(user_id: UUID, *, chave: bytes | None = None) -> bytes:
    """Calcula o HMAC-SHA256 do UUID do usuário, usando a chave do settings.

    O parâmetro `chave` existe pra testes — em produção sempre usa a chave do env.
    """
    if chave is None:
        chave = get_settings().autor_hmac_key.encode()
    return _hmac.new(chave, str(user_id).encode(), hashlib.sha256).digest()
