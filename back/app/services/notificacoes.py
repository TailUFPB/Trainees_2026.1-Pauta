# back/app/services/notificacoes.py
# ─────────────────────────────────────────────────────────────────────
# Service de notificações — a lógica de negócio
#
# No padrão do projeto:
# router  → recebe a requisição HTTP e valida os dados
# service → contém a lógica (o que fazer com os dados)
# 
# O service enfileira as tarefas no Celery.
# O Worker (processo separado) processa a fila e faz o envio real.
# ─────────────────────────────────────────────────────────────────────

import logging
from app.workers.tasks import (
    task_push_problema_novo,
    task_push_problema_resolvido,
    task_push_politico_atualizado,
    task_push_multiplos,
    task_email_problema_novo,
    task_email_problema_resolvido,
    task_email_politico_atualizado,
)

logger = logging.getLogger(__name__)


def service_problema_criado(evento) -> dict:
    """
    Decide quais canais usar e enfileira as tarefas.
    Retorna imediatamente — o Worker faz o envio em background.
    """
    canais = []

    if evento.token_fcm:
        task_push_problema_novo.delay(
            token_fcm=evento.token_fcm,
            rua=evento.rua,
            tipo=evento.tipo,
            distancia_metros=evento.distancia_metros,
            problema_id=evento.problema_id,
        )
        canais.append("push")
        logger.info(f"Push enfileirado | problema: {evento.problema_id}")

    if evento.email:
        task_email_problema_novo.delay(
            email=evento.email,
            rua=evento.rua,
            tipo=evento.tipo,
            distancia_metros=evento.distancia_metros,
        )
        canais.append("email")
        logger.info(f"Email enfileirado | problema: {evento.problema_id}")

    return {
        "status": "enfileirado",
        "problema_id": evento.problema_id,
        "canais": canais,
    }


def service_problema_resolvido(evento) -> dict:
    canais = []

    if evento.token_fcm:
        task_push_problema_resolvido.delay(
            token_fcm=evento.token_fcm,
            rua=evento.rua,
            tipo=evento.tipo,
            responsavel=evento.responsavel,
            problema_id=evento.problema_id,
        )
        canais.append("push")

    if evento.email:
        task_email_problema_resolvido.delay(
            email=evento.email,
            rua=evento.rua,
            tipo=evento.tipo,
            responsavel=evento.responsavel,
        )
        canais.append("email")

    return {
        "status": "enfileirado",
        "problema_id": evento.problema_id,
        "canais": canais,
    }


def service_politico_atualizado(evento) -> dict:
    canais = []

    if evento.token_fcm:
        task_push_politico_atualizado.delay(
            token_fcm=evento.token_fcm,
            nome_politico=evento.nome_politico,
            tipo_atualizacao=evento.tipo_atualizacao,
            politico_id=evento.politico_id,
        )
        canais.append("push")

    if evento.email:
        task_email_politico_atualizado.delay(
            email=evento.email,
            nome_politico=evento.nome_politico,
            tipo_atualizacao=evento.tipo_atualizacao,
            descricao=evento.descricao,
        )
        canais.append("email")

    return {
        "status": "enfileirado",
        "politico_id": evento.politico_id,
        "canais": canais,
    }


def service_notificar_regiao(evento) -> dict:
    task_push_multiplos.delay(
        tokens=evento.tokens_fcm,
        rua=evento.rua,
        tipo=evento.tipo,
        distancia_metros=evento.distancia_metros,
        problema_id=evento.problema_id,
    )

    logger.info(
        f"Multicast enfileirado | problema: {evento.problema_id} "
        f"| destinatários: {len(evento.tokens_fcm)}"
    )

    return {
        "status": "enfileirado",
        "problema_id": evento.problema_id,
        "destinatarios": len(evento.tokens_fcm),
    }
