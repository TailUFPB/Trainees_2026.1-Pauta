from sqlalchemy import select

from app.models.evento import EventoOutbox


def test_problema_criado_registra_evento_no_outbox(client, db):
    resp = client.post(
        "/notificacoes/problema-criado",
        json={
            "problema_id": "prob-1",
            "tipo": "buraco",
            "rua": "Rua das Flores",
            "lat": -7.12,
            "lng": -34.88,
            "severidade": "critica",
            "confianca": 0.91,
        },
    )

    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "registrado_no_outbox"
    assert body["tipo"] == "problema.criado"
    assert body["prioridade"] == "alta"

    evento = db.scalars(select(EventoOutbox)).one()
    assert evento.tipo == "problema.criado"
    assert evento.prioridade == "alta"
    assert evento.payload["problema_id"] == "prob-1"
    assert evento.payload["lat"] == -7.12


def test_problema_criado_exige_geo_ou_destinatario(client):
    resp = client.post(
        "/notificacoes/problema-criado",
        json={"problema_id": "prob-1", "tipo": "buraco"},
    )

    assert resp.status_code == 422
    assert "lat/lng" in resp.json()["detail"]


def test_worker_processa_outbox_com_destinatarios_explicitos(db, monkeypatch):
    from app.workers import tasks

    push_calls = []
    email_calls = []

    class PushTask:
        def delay(self, **kwargs):
            push_calls.append(kwargs)

    class EmailTask:
        def delay(self, **kwargs):
            email_calls.append(kwargs)

    monkeypatch.setattr(tasks, "task_push_multiplos", PushTask())
    monkeypatch.setattr(tasks, "task_email_problema_novo", EmailTask())

    evento = EventoOutbox(
        tipo="problema.criado",
        prioridade="alta",
        payload={
            "problema_id": "prob-1",
            "tipo": "buraco",
            "rua": "Rua das Flores",
            "distancia_metros": 300,
            "tokens_fcm": ["token-a", "token-b"],
            "emails": ["cidadao@teste.com"],
        },
    )
    db.add(evento)
    db.commit()

    resultado = tasks.task_processar_eventos_outbox.run(limite=10)

    db.refresh(evento)
    assert resultado == {"processados": 1, "falhas": 0, "envios_enfileirados": 3}
    assert evento.processado_em is not None
    assert push_calls[0]["tokens"] == ["token-a", "token-b"]
    assert email_calls[0]["email"] == "cidadao@teste.com"
