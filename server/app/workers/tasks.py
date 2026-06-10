import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, select

from app.db.session import SessionLocal
from app.models.evento import EventoOutbox
from app.models.user import User
from app.services.notificacoes_internas import canal_habilitado, criar_notificacao
from app.services.usuarios_geo import (
    DestinatarioNotificacao,
    buscar_destinatarios_por_politico,
    buscar_destinatarios_por_problema,
    buscar_usuarios_por_raio,
    raio_para_tipo,
)
from app.workers.celery_app import celery
from app.workers.providers.email_sender import (
    enviar_email,
    template_politico_atualizado,
    template_problema_novo,
    template_problema_resolvido,
)
from app.workers.providers.fcm import enviar_push, enviar_push_multiplos

logger = logging.getLogger(__name__)

MAX_TENTATIVAS_OUTBOX = 3
MULTICAST_FCM_LIMITE = 500


def _lista(payload: dict, chave: str) -> list[str]:
    valor = payload.get(chave) or []
    if isinstance(valor, str):
        return [valor]
    return [item for item in valor if item]


def _destinatarios_explicitos(payload: dict) -> tuple[list[str], list[str]]:
    tokens = _lista(payload, "tokens_fcm")
    emails = _lista(payload, "emails")
    if token := payload.get("token_fcm"):
        tokens.append(token)
    if email := payload.get("email"):
        emails.append(email)
    return list(dict.fromkeys(tokens)), list(dict.fromkeys(emails))


def _distancia(destinatario: DestinatarioNotificacao | None, payload: dict) -> int:
    if destinatario and destinatario.distancia_metros is not None:
        return destinatario.distancia_metros
    return int(payload.get("distancia_metros") or 0)


def _uuid_payload(payload: dict, chave: str) -> UUID:
    return UUID(str(payload[chave]))


def _origem_evento_id(payload: dict) -> UUID:
    return UUID(str(payload["_origem_evento_id"]))


def _user_ids_payload(payload: dict) -> list[UUID]:
    bruto = payload.get("user_ids") or []
    ids = [bruto] if isinstance(bruto, str) else list(bruto)
    if user_id := payload.get("user_id"):
        ids.append(user_id)
    resultado = []
    for valor in ids:
        try:
            resultado.append(UUID(str(valor)))
        except (TypeError, ValueError):
            logger.warning("Ignorando user_id invalido em payload de notificacao: %r", valor)
    return list(dict.fromkeys(resultado))


def _destinatarios_por_user_ids(db, payload: dict) -> list[DestinatarioNotificacao]:
    user_ids = _user_ids_payload(payload)
    if not user_ids:
        return []
    token_fcm = User.prefs_notificacao.op("->>")("token_fcm").label("token_fcm")
    rows = db.execute(
        select(User.id, User.email, token_fcm, User.prefs_notificacao).where(User.id.in_(user_ids))
    ).all()
    return [
        DestinatarioNotificacao(
            user_id=user_id,
            email=email,
            token_fcm=token_fcm,
            prefs_notificacao=prefs_notificacao or {},
        )
        for user_id, email, token_fcm, prefs_notificacao in rows
    ]


def _dedupe_destinatarios(destinatarios: list[DestinatarioNotificacao]) -> list[DestinatarioNotificacao]:
    vistos: set[UUID] = set()
    resultado = []
    for destinatario in destinatarios:
        if destinatario.user_id in vistos:
            continue
        vistos.add(destinatario.user_id)
        resultado.append(destinatario)
    return resultado


def _prefs(destinatario: DestinatarioNotificacao, chave: str) -> bool:
    return canal_habilitado(destinatario.prefs_notificacao, chave)


def _canais_destinatario(destinatario: DestinatarioNotificacao) -> dict:
    return {
        "interna": "criada" if _prefs(destinatario, "interna") else "desativada",
        "email": (
            "pendente"
            if destinatario.email and _prefs(destinatario, "email")
            else "desativado_ou_indisponivel"
        ),
        "push": (
            "pendente"
            if destinatario.token_fcm and _prefs(destinatario, "push")
            else "desativado_ou_indisponivel"
        ),
    }


def _criar_interna_problema_novo(db, destinatario: DestinatarioNotificacao, payload: dict) -> int:
    if not _prefs(destinatario, "interna") or not _prefs(destinatario, "problemas_perto"):
        return 0
    tipo = payload.get("tipo") or payload.get("tipo_problema") or "problema"
    rua = payload.get("rua") or "regiao informada"
    distancia = _distancia(destinatario, payload)
    criada = criar_notificacao(
        db,
        origem_evento_id=_origem_evento_id(payload),
        user_id=destinatario.user_id,
        tipo="problema.criado",
        titulo="Novo problema perto de voce",
        mensagem=f"{tipo} reportado em {rua}, a {distancia}m de voce.",
        link_destino=f"/mapa?problema_id={payload.get('problema_id')}",
        canais=_canais_destinatario(destinatario),
        dados={
            "problema_id": payload.get("problema_id"),
            "tipo": tipo,
            "rua": rua,
            "distancia_metros": distancia,
        },
    )
    return int(criada)


def _criar_interna_problema_status(db, destinatario: DestinatarioNotificacao, payload: dict) -> int:
    if not _prefs(destinatario, "interna"):
        return 0
    tipo = payload.get("tipo") or "problema"
    rua = payload.get("rua") or "local informado"
    responsavel = payload.get("responsavel") or payload.get("resolvido_por") or "responsavel"
    criada = criar_notificacao(
        db,
        origem_evento_id=_origem_evento_id(payload),
        user_id=destinatario.user_id,
        tipo="problema.status_alterado",
        titulo="Problema resolvido",
        mensagem=f"O {tipo} em {rua} foi resolvido por {responsavel}.",
        link_destino=f"/mapa?problema_id={payload.get('problema_id')}",
        canais=_canais_destinatario(destinatario),
        dados={
            "problema_id": payload.get("problema_id"),
            "tipo": tipo,
            "rua": rua,
            "responsavel": responsavel,
        },
    )
    return int(criada)


def _criar_interna_politico(db, destinatario: DestinatarioNotificacao, payload: dict) -> int:
    if not _prefs(destinatario, "interna") or not _prefs(destinatario, "politicos"):
        return 0
    nome = payload.get("nome_politico") or "politico acompanhado"
    tipo_atualizacao = payload.get("tipo_atualizacao") or "Atualizacao"
    criada = criar_notificacao(
        db,
        origem_evento_id=_origem_evento_id(payload),
        user_id=destinatario.user_id,
        tipo="politico.atualizado",
        titulo=f"Novidade sobre {nome}",
        mensagem=f"{tipo_atualizacao}. Toque para ver mais.",
        link_destino=f"/candidatos?politico_id={payload.get('politico_id')}",
        canais=_canais_destinatario(destinatario),
        dados={
            "politico_id": payload.get("politico_id"),
            "nome_politico": nome,
            "tipo_atualizacao": tipo_atualizacao,
        },
    )
    return int(criada)


def _criar_interna_teste(db, destinatario: DestinatarioNotificacao, payload: dict) -> int:
    if not _prefs(destinatario, "interna"):
        return 0
    criada = criar_notificacao(
        db,
        origem_evento_id=_origem_evento_id(payload),
        user_id=destinatario.user_id,
        tipo="notificacao.teste",
        titulo=payload.get("titulo") or "Notificacao de teste",
        mensagem=payload.get("mensagem") or "Sua central interna de notificacoes esta funcionando.",
        link_destino="/conta/notificacoes",
        canais=_canais_destinatario(destinatario),
        dados={"origem": "teste"},
    )
    return int(criada)


def _enfileirar_push_multicast(tokens: list[str], payload: dict) -> int:
    if not tokens:
        return 0
    total = 0
    for inicio in range(0, len(tokens), MULTICAST_FCM_LIMITE):
        lote = tokens[inicio : inicio + MULTICAST_FCM_LIMITE]
        task_push_multiplos.delay(
            tokens=lote,
            rua=payload.get("rua") or "regiao informada",
            tipo=payload.get("tipo") or payload.get("tipo_problema") or "problema",
            distancia_metros=int(payload.get("distancia_metros") or 0),
            problema_id=str(payload["problema_id"]),
        )
        total += len(lote)
    return total


def _enfileirar_problema_novo_destinatarios(
    db,
    destinatarios: list[DestinatarioNotificacao],
    payload: dict,
) -> int:
    total = 0
    for destinatario in destinatarios:
        distancia_metros = _distancia(destinatario, payload)
        total += _criar_interna_problema_novo(db, destinatario, payload)
        if destinatario.token_fcm and _prefs(destinatario, "push"):
            task_push_problema_novo.delay(
                token_fcm=destinatario.token_fcm,
                rua=payload.get("rua") or "regiao informada",
                tipo=payload.get("tipo") or payload.get("tipo_problema") or "problema",
                distancia_metros=distancia_metros,
                problema_id=str(payload["problema_id"]),
            )
            total += 1
        if destinatario.email and _prefs(destinatario, "email"):
            task_email_problema_novo.delay(
                email=destinatario.email,
                rua=payload.get("rua") or "regiao informada",
                tipo=payload.get("tipo") or payload.get("tipo_problema") or "problema",
                distancia_metros=distancia_metros,
            )
            total += 1
    return total


def _processar_problema_criado(db, payload: dict) -> int:
    tokens, emails = _destinatarios_explicitos(payload)
    total = _enfileirar_push_multicast(tokens, payload)
    destinatarios_explicitos = _destinatarios_por_user_ids(db, payload)
    for email in emails:
        task_email_problema_novo.delay(
            email=email,
            rua=payload.get("rua") or "regiao informada",
            tipo=payload.get("tipo") or payload.get("tipo_problema") or "problema",
            distancia_metros=int(payload.get("distancia_metros") or 0),
        )
        total += 1

    if payload.get("lat") is None or payload.get("lng") is None:
        return total + _enfileirar_problema_novo_destinatarios(
            db, destinatarios_explicitos, payload
        )

    raio_metros = int(payload.get("raio_metros") or raio_para_tipo(payload.get("tipo")))
    destinatarios = _dedupe_destinatarios(
        destinatarios_explicitos
        + buscar_usuarios_por_raio(
            db,
            lat=float(payload["lat"]),
            lng=float(payload["lng"]),
            raio_metros=raio_metros,
        )
    )
    return total + _enfileirar_problema_novo_destinatarios(db, destinatarios, payload)


def _processar_problema_status(db, payload: dict) -> int:
    tokens, emails = _destinatarios_explicitos(payload)
    total = 0
    for token in tokens:
        task_push_problema_resolvido.delay(
            token_fcm=token,
            rua=payload.get("rua") or "local informado",
            tipo=payload.get("tipo") or "problema",
            responsavel=payload.get("responsavel") or payload.get("resolvido_por") or "responsavel",
            problema_id=str(payload["problema_id"]),
        )
        total += 1
    for email in emails:
        task_email_problema_resolvido.delay(
            email=email,
            rua=payload.get("rua") or "local informado",
            tipo=payload.get("tipo") or "problema",
            responsavel=payload.get("responsavel") or payload.get("resolvido_por") or "responsavel",
        )
        total += 1

    if payload.get("problema_id") is None:
        return total

    destinatarios = _dedupe_destinatarios(
        buscar_destinatarios_por_problema(
            db,
            problema_id=_uuid_payload(payload, "problema_id"),
        )
        + _destinatarios_por_user_ids(db, payload)
    )
    for destinatario in destinatarios:
        total += _criar_interna_problema_status(db, destinatario, payload)
        if destinatario.token_fcm and _prefs(destinatario, "push"):
            task_push_problema_resolvido.delay(
                token_fcm=destinatario.token_fcm,
                rua=payload.get("rua") or "local informado",
                tipo=payload.get("tipo") or "problema",
                responsavel=payload.get("responsavel")
                or payload.get("resolvido_por")
                or "responsavel",
                problema_id=str(payload["problema_id"]),
            )
            total += 1
        if destinatario.email and _prefs(destinatario, "email"):
            task_email_problema_resolvido.delay(
                email=destinatario.email,
                rua=payload.get("rua") or "local informado",
                tipo=payload.get("tipo") or "problema",
                responsavel=payload.get("responsavel")
                or payload.get("resolvido_por")
                or "responsavel",
            )
            total += 1
    return total


def _processar_politico(db, payload: dict) -> int:
    tokens, emails = _destinatarios_explicitos(payload)
    total = 0
    for token in tokens:
        task_push_politico_atualizado.delay(
            token_fcm=token,
            nome_politico=payload["nome_politico"],
            tipo_atualizacao=payload["tipo_atualizacao"],
            politico_id=str(payload["politico_id"]),
        )
        total += 1
    for email in emails:
        task_email_politico_atualizado.delay(
            email=email,
            nome_politico=payload["nome_politico"],
            tipo_atualizacao=payload["tipo_atualizacao"],
            descricao=payload.get("descricao") or "",
        )
        total += 1

    if payload.get("politico_id") is None:
        return total

    destinatarios = _dedupe_destinatarios(
        buscar_destinatarios_por_politico(
            db,
            politico_id=_uuid_payload(payload, "politico_id"),
        )
        + _destinatarios_por_user_ids(db, payload)
    )
    for destinatario in destinatarios:
        total += _criar_interna_politico(db, destinatario, payload)
        if destinatario.token_fcm and _prefs(destinatario, "push"):
            task_push_politico_atualizado.delay(
                token_fcm=destinatario.token_fcm,
                nome_politico=payload["nome_politico"],
                tipo_atualizacao=payload["tipo_atualizacao"],
                politico_id=str(payload["politico_id"]),
            )
            total += 1
        if destinatario.email and _prefs(destinatario, "email"):
            task_email_politico_atualizado.delay(
                email=destinatario.email,
                nome_politico=payload["nome_politico"],
                tipo_atualizacao=payload["tipo_atualizacao"],
                descricao=payload.get("descricao") or "",
            )
            total += 1
    return total


def _processar_notificacao_teste(db, payload: dict) -> int:
    total = 0
    for destinatario in _destinatarios_por_user_ids(db, payload):
        total += _criar_interna_teste(db, destinatario, payload)
    return total


def _processar_evento(db, evento: EventoOutbox) -> int:
    payload = {**(evento.payload or {}), "_origem_evento_id": evento.id}
    if evento.tipo == "problema.criado":
        return _processar_problema_criado(db, payload)
    if evento.tipo == "problema.status_alterado":
        return _processar_problema_status(db, payload)
    if evento.tipo in {"politico.status_alterado", "politico.atualizado"}:
        return _processar_politico(db, payload)
    if evento.tipo == "notificacao.teste":
        return _processar_notificacao_teste(db, payload)
    logger.info("Evento sem consumidor de notificacao | id=%s tipo=%s", evento.id, evento.tipo)
    return 0


@celery.task(name="app.workers.tasks.task_processar_eventos_outbox")
def task_processar_eventos_outbox(limite: int = 50) -> dict:
    prioridade_ordem = case(
        (EventoOutbox.prioridade == "alta", 0),
        (EventoOutbox.prioridade == "media", 1),
        else_=2,
    )
    processados = 0
    falhas = 0
    envios_enfileirados = 0

    with SessionLocal() as db:
        eventos = db.scalars(
            select(EventoOutbox)
            .where(EventoOutbox.processado_em.is_(None))
            .where(EventoOutbox.tentativas < MAX_TENTATIVAS_OUTBOX)
            .order_by(prioridade_ordem, EventoOutbox.criado_em)
            .limit(limite)
            .with_for_update(skip_locked=True)
        ).all()

        for evento in eventos:
            try:
                envios = _processar_evento(db, evento)
                evento.processado_em = datetime.now(UTC)
                envios_enfileirados += envios
                processados += 1
                logger.info(
                    "Evento outbox processado | id=%s tipo=%s envios=%s",
                    evento.id,
                    evento.tipo,
                    envios,
                )
            except Exception:
                evento.tentativas = (evento.tentativas or 0) + 1
                falhas += 1
                logger.exception(
                    "Falha ao processar evento outbox | id=%s tipo=%s tentativas=%s",
                    evento.id,
                    evento.tipo,
                    evento.tentativas,
                )
            finally:
                db.commit()

    return {
        "processados": processados,
        "falhas": falhas,
        "envios_enfileirados": envios_enfileirados,
    }


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_push_problema_novo(self, token_fcm, rua, tipo, distancia_metros, problema_id):
    try:
        enviado = enviar_push(
            token_fcm=token_fcm,
            titulo="Novo problema perto de voce!",
            mensagem=f"{tipo} reportado na {rua}, a {distancia_metros}m de voce.",
            dados={"tipo": "problema_novo", "problema_id": problema_id, "tela": "mapa"},
        )
        if not enviado:
            raise RuntimeError("Push nao enviado.")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_push_problema_resolvido(self, token_fcm, rua, tipo, responsavel, problema_id):
    try:
        enviado = enviar_push(
            token_fcm=token_fcm,
            titulo="Problema resolvido!",
            mensagem=f"O {tipo} na {rua} foi resolvido por {responsavel}.",
            dados={
                "tipo": "problema_resolvido",
                "problema_id": problema_id,
                "tela": "problema_detalhe",
            },
        )
        if not enviado:
            raise RuntimeError("Push nao enviado.")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_push_politico_atualizado(self, token_fcm, nome_politico, tipo_atualizacao, politico_id):
    try:
        enviado = enviar_push(
            token_fcm=token_fcm,
            titulo=f"Novidade sobre {nome_politico}",
            mensagem=f"{tipo_atualizacao}. Toque para ver mais.",
            dados={
                "tipo": "politico_atualizado",
                "politico_id": politico_id,
                "tela": "perfil_politico",
            },
        )
        if not enviado:
            raise RuntimeError("Push nao enviado.")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_push_multiplos(self, tokens, rua, tipo, distancia_metros, problema_id):
    try:
        resultado = enviar_push_multiplos(
            tokens=tokens,
            titulo="Novo problema perto de voce!",
            mensagem=f"{tipo} reportado na {rua}, a {distancia_metros}m de voce.",
            dados={"tipo": "problema_novo", "problema_id": problema_id, "tela": "mapa"},
        )
        if resultado["falha"] == len(tokens):
            raise RuntimeError("Nenhum push multicast foi enviado.")
        logger.info("Multicast | sucesso=%s falha=%s", resultado["sucesso"], resultado["falha"])
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_email_problema_novo(self, email, rua, tipo, distancia_metros):
    try:
        enviado = enviar_email(
            destinatario=email,
            assunto=f"Novo {tipo} reportado perto de voce",
            corpo_html=template_problema_novo(rua, tipo, distancia_metros),
        )
        if not enviado:
            raise RuntimeError("Email nao enviado.")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_email_problema_resolvido(self, email, rua, tipo, responsavel):
    try:
        enviado = enviar_email(
            destinatario=email,
            assunto=f"O {tipo} na {rua} foi resolvido",
            corpo_html=template_problema_resolvido(rua, tipo, responsavel),
        )
        if not enviado:
            raise RuntimeError("Email nao enviado.")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def task_email_politico_atualizado(self, email, nome_politico, tipo_atualizacao, descricao):
    try:
        enviado = enviar_email(
            destinatario=email,
            assunto=f"Novidade sobre {nome_politico}",
            corpo_html=template_politico_atualizado(nome_politico, tipo_atualizacao, descricao),
        )
        if not enviado:
            raise RuntimeError("Email nao enviado.")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
