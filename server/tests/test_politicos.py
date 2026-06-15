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


def test_listar_default_retorna_no_maximo_50(client, db):
    # Paginação real: default é uma página de 50.
    for i in range(60):
        db.add(Politico(id=uuid.uuid4(), nome=f"P{i:03d}", municipio="X"))
    db.commit()

    resp = client.get("/politicos")

    assert resp.status_code == 200
    assert len(resp.json()) == 50


def test_listar_paginacao_disjunta_por_offset(client, db):
    for i in range(60):
        db.add(Politico(id=uuid.uuid4(), nome=f"P{i:03d}", municipio="X"))
    db.commit()

    pg1 = client.get("/politicos?limite=25&offset=0").json()
    pg2 = client.get("/politicos?limite=25&offset=25").json()

    assert len(pg1) == 25 and len(pg2) == 25
    assert {p["id"] for p in pg1}.isdisjoint({p["id"] for p in pg2})


def test_listar_param_fora_dos_limites_retorna_422(client):
    # limite/offset fora dos limites devem falhar na validação, não chegar ao DB.
    assert client.get("/politicos?limite=0").status_code == 422
    assert client.get("/politicos?limite=1000").status_code == 422
    assert client.get("/politicos?offset=-1").status_code == 422
