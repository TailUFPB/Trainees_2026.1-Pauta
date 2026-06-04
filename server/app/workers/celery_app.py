# back/app/workers/celery_app.py
# ─────────────────────────────────────────────────────────────────────
# Configuração do Celery integrada ao projeto
#
# Usa as configurações do projeto (app.core.config) em vez de
# variáveis separadas — segue o padrão do pyproject.toml
# ─────────────────────────────────────────────────────────────────────

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis vem do docker-compose — mesma rede do banco
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "pauta_notificacoes",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.tasks"],  # onde estão as tarefas
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_acks_late=True,               # remove da fila só após confirmar sucesso
    task_reject_on_worker_lost=True,   # volta pra fila se o Worker cair
    worker_max_tasks_per_child=1000,   # reinicia Worker após 1000 tarefas
)
