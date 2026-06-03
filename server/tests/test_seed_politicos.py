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
