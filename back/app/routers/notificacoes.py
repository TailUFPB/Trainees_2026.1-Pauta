# back/app/routers/notificacoes.py
# ─────────────────────────────────────────────────────────────────────
# Router de notificações do Pauta
# Segue o mesmo padrão dos outros routers do projeto:
# politicos.py, problemas.py, recomendacoes.py, usuarios.py
#
# O que este router faz:
# - Recebe eventos de outros módulos (LLM, scraping, backend)
# - Enfileira tarefas no Celery para envio assíncrono
# - Não envia nada diretamente — o Worker cuida disso
# ─────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.notificacoes import (
    service_problema_criado,
    service_problema_resolvido,
    service_politico_atualizado,
    service_notificar_regiao,
)

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])


# ─────────────────────────────────────────────────────────────────────
# SCHEMAS — definem o formato dos dados que chegam nos endpoints
# Pydantic valida automaticamente — se faltar campo retorna erro 422
# ─────────────────────────────────────────────────────────────────────

class EventoProblemaNotificacao(BaseModel):
    problema_id: str
    rua: str
    tipo: str                        # buraco | alagamento | entulho | iluminacao
    distancia_metros: int
    token_fcm: Optional[str] = None  # token do celular do usuário
    email: Optional[str] = None      # email do usuário

class EventoProblemaResolvido(BaseModel):
    problema_id: str
    rua: str
    tipo: str
    responsavel: str                 # ONG ou vereador que resolveu
    token_fcm: Optional[str] = None
    email: Optional[str] = None

class EventoPoliticoAtualizado(BaseModel):
    politico_id: str
    nome_politico: str
    tipo_atualizacao: str            # novo_projeto | status_alterado | noticia_nova
    descricao: str
    token_fcm: Optional[str] = None
    email: Optional[str] = None

class EventoNotificarRegiao(BaseModel):
    problema_id: str
    rua: str
    tipo: str
    distancia_metros: int
    tokens_fcm: list[str]            # lista de tokens de todos os usuários próximos


# ─────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────

@router.post("/problema-criado")
def problema_criado(evento: EventoProblemaNotificacao):
    """
    Notifica usuários sobre novo problema de infraestrutura.

    Chamado por:
    - Módulo de LLM quando severidade = alta ou crítica com confiança >= 0.6
    - Backend quando problema é cadastrado manualmente
    """
    if not evento.token_fcm and not evento.email:
        raise HTTPException(
            status_code=400,
            detail="Forneça pelo menos token_fcm ou email."
        )
    return service_problema_criado(evento)


@router.post("/problema-resolvido")
def problema_resolvido(evento: EventoProblemaResolvido):
    """
    Notifica usuários que um problema foi resolvido.

    Chamado por:
    - Backend quando ONG ou vereador marca problema como resolvido
    """
    if not evento.token_fcm and not evento.email:
        raise HTTPException(
            status_code=400,
            detail="Forneça pelo menos token_fcm ou email."
        )
    return service_problema_resolvido(evento)


@router.post("/politico-atualizado")
def politico_atualizado(evento: EventoPoliticoAtualizado):
    """
    Notifica usuários sobre atualização de político.

    Chamado por:
    - Módulo de scraping quando detecta mudança no político
    - Destinatários já filtrados por similaridade de cosseno pelo sistema de ML
    """
    if not evento.token_fcm and not evento.email:
        raise HTTPException(
            status_code=400,
            detail="Forneça pelo menos token_fcm ou email."
        )
    return service_politico_atualizado(evento)


@router.post("/notificar-regiao")
def notificar_regiao(evento: EventoNotificarRegiao):
    """
    Envia push para múltiplos usuários de uma região ao mesmo tempo.

    Chamado por:
    - Backend quando identifica todos os usuários num raio do problema
    - Mais eficiente que chamar /problema-criado em loop
    """
    if not evento.tokens_fcm:
        raise HTTPException(
            status_code=400,
            detail="Lista de tokens não pode ser vazia."
        )
    return service_notificar_regiao(evento)
