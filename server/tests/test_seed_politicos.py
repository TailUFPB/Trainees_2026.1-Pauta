from pathlib import Path

from sqlalchemy import select

from app.cli.seed_politicos import seed_from_csv
from app.models.politico import Politico


def _escrever_csv(tmp_path: Path, linhas: list[str]) -> Path:
    p = tmp_path / "perfil.csv"
    conteudo = "municipio,nome,partido,foto,url_perfil\n" + "\n".join(linhas) + "\n"
    p.write_text(conteudo, encoding="utf-8")
    return p


def test_importa_linha_normal(tmp_path, db):
    path = _escrever_csv(tmp_path, ["JP,Ana Silva,PT,http://x/a.png,http://x/perfil-ana"])

    resumo = seed_from_csv(path, db)

    assert resumo == {"importados": 1, "atualizados": 0, "total": 1}
    p = db.scalar(select(Politico))
    assert p.municipio == "JP"
    assert p.nome == "Ana Silva"
    assert p.partido == "PT"
    assert p.foto_url == "http://x/a.png"
    assert p.fonte_url == "http://x/perfil-ana"


def test_sentinels_viram_null(tmp_path, db):
    path = _escrever_csv(tmp_path, ["JP,Bia,sem_partido,http://x/b.png,sem_perfil"])

    seed_from_csv(path, db)

    p = db.scalar(select(Politico))
    assert p.partido is None
    assert p.fonte_url is None
    assert p.foto_url == "http://x/b.png"  # foto não é sentinel — fica


def test_string_vazia_vira_null(tmp_path, db):
    path = _escrever_csv(tmp_path, ["JP,Caio,,http://x/c.png,"])

    seed_from_csv(path, db)

    p = db.scalar(select(Politico))
    assert p.partido is None
    assert p.fonte_url is None


def test_idempotente_segunda_execucao_atualiza(tmp_path, db):
    path = _escrever_csv(tmp_path, [
        "JP,Ana,PT,http://x/a.png,http://x/p-ana",
        "CG,Caio,MDB,http://x/c.png,sem_perfil",
    ])
    r1 = seed_from_csv(path, db)
    assert r1 == {"importados": 2, "atualizados": 0, "total": 2}

    # Reescreve mesmo CSV trocando partido/foto/url da Ana
    path.write_text(
        "municipio,nome,partido,foto,url_perfil\n"
        "JP,Ana,PSB,http://x/a2.png,http://x/p-ana-v2\n"
        "CG,Caio,MDB,http://x/c.png,sem_perfil\n",
        encoding="utf-8",
    )
    r2 = seed_from_csv(path, db)

    assert r2 == {"importados": 0, "atualizados": 2, "total": 2}
    ana = db.scalar(select(Politico).where(Politico.nome == "Ana"))
    assert ana.partido == "PSB"
    assert ana.foto_url == "http://x/a2.png"
    assert ana.fonte_url == "http://x/p-ana-v2"


def test_nome_com_virgula_entre_aspas(tmp_path, db):
    # Casos reais do CSV (linhas 94 e 96 do df_perfil.csv)
    path = tmp_path / "x.csv"
    path.write_text(
        'municipio,nome,partido,foto,url_perfil\n'
        'Santa Rita,"Brunno Inocêncio da Nobrega Silva (Bruno, o filho de Cicinha)",PT,http://x/b.png,sem_perfil\n'
        'Santa Rita,"Fagner Francelino dos Santos (Boquinha, filho de Walter Cruz)",PSB,http://x/f.png,sem_perfil\n',
        encoding="utf-8",
    )

    resumo = seed_from_csv(path, db)

    assert resumo["importados"] == 2
    nomes = {p.nome for p in db.scalars(select(Politico))}
    assert "Brunno Inocêncio da Nobrega Silva (Bruno, o filho de Cicinha)" in nomes
    assert "Fagner Francelino dos Santos (Boquinha, filho de Walter Cruz)" in nomes
