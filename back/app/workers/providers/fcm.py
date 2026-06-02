# back/app/workers/providers/fcm.py
# Integração com Firebase Cloud Messaging
# Igual ao providers/fcm.py do projeto standalone — só mudou o caminho

import os
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def _inicializar_firebase():
    if not firebase_admin._apps:
        caminho = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
        if not os.path.exists(caminho):
            logger.warning(f"Credenciais Firebase não encontradas: {caminho}")
            return False
        firebase_admin.initialize_app(credentials.Certificate(caminho))
    return True

def enviar_push(token_fcm: str, titulo: str, mensagem: str, dados: dict = None) -> bool:
    if not _inicializar_firebase():
        return False
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=titulo, body=mensagem),
            data=dados or {},
            token=token_fcm,
        )
        response = messaging.send(message)
        logger.info(f"Push enviado | ID: {response}")
        return True
    except messaging.UnregisteredError:
        logger.error(f"Token FCM inválido: {token_fcm[:20]}...")
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar push: {e}")
        raise

def enviar_push_multiplos(tokens: list, titulo: str, mensagem: str, dados: dict = None) -> dict:
    if not _inicializar_firebase():
        return {"sucesso": 0, "falha": len(tokens)}
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=titulo, body=mensagem),
            data=dados or {},
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        return {"sucesso": response.success_count, "falha": response.failure_count}
    except Exception as e:
        logger.error(f"Erro no multicast: {e}")
        raise
