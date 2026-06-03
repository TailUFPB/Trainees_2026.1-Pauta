import uuid

from app.models.politico import Politico


def test_listar_inclui_foto_e_url_perfil(client, db):
    db.add_all([
        Politico(
            id=uuid.uuid4(),
            nome="Ana",
            municipio="JP",
            partido="PT",
            foto_url="http://x/a.png",
            fonte_url="http://x/perfil-ana",
        ),
        Politico(
            id=uuid.uuid4(),
            nome="Bia",
            municipio="JP",
            foto_url=None,
            fonte_url=None,
        ),
    ])
    db.commit()

    resp = client.get("/politicos")

    assert resp.status_code == 200
    por_nome = {p["nome"]: p for p in resp.json()}
    assert por_nome["Ana"]["foto_url"] == "http://x/a.png"
    assert por_nome["Ana"]["url_perfil"] == "http://x/perfil-ana"
    assert por_nome["Bia"]["foto_url"] is None
    assert por_nome["Bia"]["url_perfil"] is None


def test_limite_default_acomoda_97_politicos(client, db):
    # Garante que o default cobre o universo atual sem precisar de ?limite=
    for i in range(150):
        db.add(Politico(id=uuid.uuid4(), nome=f"P{i:03d}", municipio="X"))
    db.commit()

    resp = client.get("/politicos")

    assert resp.status_code == 200
    assert len(resp.json()) == 150  # default 200 acomoda


def test_seguir_idempotente_quando_ja_segue(client, db, auth_headers):
    politico = Politico(id=uuid.uuid4(), nome="Pol A", municipio="JP")
    db.add(politico)
    db.commit()

    primeira = client.post(f"/politicos/{politico.id}/seguir", headers=auth_headers)
    segunda = client.post(f"/politicos/{politico.id}/seguir", headers=auth_headers)
    assert primeira.status_code == 204, primeira.text
    assert segunda.status_code == 204, segunda.text


def test_seguir_politico_inexistente_retorna_404(client, auth_headers):
    resp = client.post(f"/politicos/{uuid.uuid4()}/seguir", headers=auth_headers)
    assert resp.status_code == 404
