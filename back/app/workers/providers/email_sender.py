# back/app/workers/providers/email_sender.py
# Integração com Resend para envio de emails

import os
import logging
import resend
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "notificacoes@pauta.app")

def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> bool:
    if not resend.api_key:
        logger.error("RESEND_API_KEY não configurada no .env")
        return False
    try:
        response = resend.Emails.send({
            "from": EMAIL_FROM,
            "to": [destinatario],
            "subject": assunto,
            "html": corpo_html,
        })
        logger.info(f"Email enviado para {destinatario} | ID: {response.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email para {destinatario}: {e}")
        raise

def template_problema_novo(rua, tipo, distancia_metros):
    return f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
    <h2 style="color:#e74c3c">🚧 Novo problema perto de você</h2>
    <div style="background:#f8f9fa;padding:16px;border-radius:8px">
        <strong>Tipo:</strong> {tipo}<br>
        <strong>Local:</strong> {rua}<br>
        <strong>Distância:</strong> aproximadamente {distancia_metros}m de você
    </div>
    <p>Acesse o Pauta para acompanhar a resolução.</p>
    </div>"""

def template_problema_resolvido(rua, tipo, responsavel):
    return f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
    <h2 style="color:#27ae60">✅ Problema resolvido!</h2>
    <div style="background:#f0fff4;padding:16px;border-radius:8px">
        <strong>Tipo:</strong> {tipo}<br>
        <strong>Local:</strong> {rua}<br>
        <strong>Resolvido por:</strong> {responsavel}
    </div>
    </div>"""

def template_politico_atualizado(nome_politico, tipo_atualizacao, descricao):
    return f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
    <h2 style="color:#2980b9">📋 Atualização sobre {nome_politico}</h2>
    <div style="background:#f0f4ff;padding:16px;border-radius:8px">
        <strong>Político:</strong> {nome_politico}<br>
        <strong>Atualização:</strong> {tipo_atualizacao}<br>
        <strong>Detalhes:</strong> {descricao}
    </div>
    </div>"""
