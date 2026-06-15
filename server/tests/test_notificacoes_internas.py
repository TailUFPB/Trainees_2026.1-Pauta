from sqlalchemy import select

from app.models.evento import EventoOutbox
from app.models.notificacao import Notificacao


def test_preferencias_notificacao_tem_defaults_e_salva_token(client, auth_headers):
    resp = client.get("/usuarios/me/notificacoes/preferencias", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    prefs = resp.json()["prefs_notificacao"]
    assert prefs["interna"] is True
    assert prefs["email"] is True
    assert prefs["push"] is True

    resp = client.patch(
        "/usuarios/me/notificacoes",
        headers=auth_headers,
        json={"email": False, "token_fcm": "token-demo"},
    )

    assert resp.status_code == 200, resp.text
    prefs = resp.json()["prefs_notificacao"]
    assert prefs["email"] is False
    assert prefs["token_fcm"] == "token-demo"


def test_listar_contar_e_marcar_notificacao_lida(client, auth_headers, db, user_id):
    client.get("/usuarios/me", headers=auth_headers)
    notificacao = Notificacao(
        user_id=user_id,
        tipo="usuario.atualizado",
        titulo="Teste",
        mensagem="Mensagem de teste",
        link_destino="/conta/notificacoes",
    )
    db.add(notificacao)
    db.commit()

    resp = client.get("/usuarios/me/notificacoes/contagem", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"nao_lidas": 1}

    resp = client.get("/usuarios/me/notificacoes", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 1
    assert body[0]["titulo"] == "Teste"
    assert body[0]["lida"] is False

    resp = client.patch(
        f"/usuarios/me/notificacoes/{notificacao.id}/lida",
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["lida"] is True

    resp = client.get("/usuarios/me/notificacoes/contagem", headers=auth_headers)
    assert resp.json() == {"nao_lidas": 0}


def test_rota_teste_registra_evento_para_usuario_logado(client, auth_headers, db, user_id):
    resp = client.post("/notificacoes/teste", headers=auth_headers, json={})

    assert resp.status_code == 202, resp.text
    evento = db.scalars(select(EventoOutbox)).one()
    assert evento.tipo == "notificacao.teste"
    assert evento.payload["user_ids"] == [str(user_id)]


def test_rota_teste_rejeita_titulo_maior_que_o_banco(client, auth_headers):
    resp = client.post(
        "/notificacoes/teste",
        headers=auth_headers,
        json={"titulo": "x" * 161},
    )

    assert resp.status_code == 422


def test_worker_cria_notificacao_interna_sem_email_ou_push(client, auth_headers, db, user_id):
    from app.workers import tasks

    client.patch(
        "/usuarios/me/notificacoes",
        headers=auth_headers,
        json={"email": False, "push": False},
    )
    evento = EventoOutbox(
        tipo="notificacao.teste",
        prioridade="baixa",
        payload={
            "user_ids": [str(user_id)],
            "titulo": "Teste interno",
            "mensagem": "Funcionou sem canal externo.",
            "imagem_url": "https://cdn.exemplo.com/notificacao.jpg",
        },
    )
    db.add(evento)
    db.commit()

    resultado = tasks.task_processar_eventos_outbox.run(limite=10)

    assert resultado == {"processados": 1, "falhas": 0, "envios_enfileirados": 1}
    notificacao = db.scalars(select(Notificacao)).one()
    assert notificacao.user_id == user_id
    assert notificacao.titulo == "Teste interno"
    assert notificacao.canais["interna"] == "criada"
    assert notificacao.dados["imagem_url"] == "https://cdn.exemplo.com/notificacao.jpg"


def test_worker_nao_duplica_notificacao_ao_reprocessar_evento(
    client, auth_headers, db, user_id
):
    from app.workers import tasks

    client.get("/usuarios/me", headers=auth_headers)
    evento = EventoOutbox(
        tipo="notificacao.teste",
        prioridade="baixa",
        payload={"user_ids": [str(user_id)], "titulo": "Evento idempotente"},
    )
    db.add(evento)
    db.commit()

    tasks.task_processar_eventos_outbox.run(limite=10)
    db.refresh(evento)
    evento.processado_em = None
    db.commit()
    resultado = tasks.task_processar_eventos_outbox.run(limite=10)

    assert resultado == {"processados": 1, "falhas": 0, "envios_enfileirados": 0}
    assert len(db.scalars(select(Notificacao)).all()) == 1
