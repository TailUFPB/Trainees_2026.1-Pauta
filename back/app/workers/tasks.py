# back/app/workers/tasks.py
# ─────────────────────────────────────────────────────────────────────
# Tarefas do Worker Celery
#
# Cada função @app.task é executada em background pelo Worker.
# O service chama .delay() para enfileirar — o Worker executa depois.
#
# Retentativas com backoff exponencial:
# Falhou → espera 60s → falhou → espera 120s → falhou → DLQ
# ─────────────────────────────────────────────────────────────────────

import logging
from app.workers.celery_app import celery
from app.workers.providers.fcm import enviar_push, enviar_push_multiplos
from app.workers.providers.email_sender import (
    enviar_email,
    template_problema_novo,
    template_problema_resolvido,
    template_politico_atualizado,
)

logger = logging.getLogger(__name__)


# ── PUSH ──────────────────────────────────────────────────────────────

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_push_problema_novo(self, token_fcm, rua, tipo, distancia_metros, problema_id):
    try:
        enviar_push(
            token_fcm=token_fcm,
            titulo="🚧 Novo problema perto de você!",
            mensagem=f"{tipo} reportado na {rua}, a {distancia_metros}m de você.",
            dados={"tipo": "problema_novo", "problema_id": problema_id, "tela": "mapa"},
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_push_problema_resolvido(self, token_fcm, rua, tipo, responsavel, problema_id):
    try:
        enviar_push(
            token_fcm=token_fcm,
            titulo="✅ Problema resolvido!",
            mensagem=f"O {tipo} na {rua} foi resolvido por {responsavel}.",
            dados={"tipo": "problema_resolvido", "problema_id": problema_id, "tela": "problema_detalhe"},
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_push_politico_atualizado(self, token_fcm, nome_politico, tipo_atualizacao, politico_id):
    try:
        enviar_push(
            token_fcm=token_fcm,
            titulo=f"📋 Novidade sobre {nome_politico}",
            mensagem=f"{tipo_atualizacao}. Toque para ver mais.",
            dados={"tipo": "politico_atualizado", "politico_id": politico_id, "tela": "perfil_politico"},
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_push_multiplos(self, tokens, rua, tipo, distancia_metros, problema_id):
    try:
        resultado = enviar_push_multiplos(
            tokens=tokens,
            titulo="🚧 Novo problema perto de você!",
            mensagem=f"{tipo} reportado na {rua}, a {distancia_metros}m de você.",
            dados={"tipo": "problema_novo", "problema_id": problema_id, "tela": "mapa"},
        )
        logger.info(f"Multicast | sucesso: {resultado['sucesso']} | falha: {resultado['falha']}")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ── EMAIL ─────────────────────────────────────────────────────────────

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_email_problema_novo(self, email, rua, tipo, distancia_metros):
    try:
        enviar_email(
            destinatario=email,
            assunto=f"🚧 Novo {tipo} reportado perto de você",
            corpo_html=template_problema_novo(rua, tipo, distancia_metros),
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_email_problema_resolvido(self, email, rua, tipo, responsavel):
    try:
        enviar_email(
            destinatario=email,
            assunto=f"✅ O {tipo} na {rua} foi resolvido",
            corpo_html=template_problema_resolvido(rua, tipo, responsavel),
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_email_politico_atualizado(self, email, nome_politico, tipo_atualizacao, descricao):
    try:
        enviar_email(
            destinatario=email,
            assunto=f"📋 Novidade sobre {nome_politico}",
            corpo_html=template_politico_atualizado(nome_politico, tipo_atualizacao, descricao),
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
