"""Testes do seed de vetores (embedding + cluster_id) com a garantia de integridade.

Foco: o seed OU popula todos os vereadores casados, OU aborta sem persistir nada
(elimina o risco de banco meio-populado por mismatch de chave).
"""
import csv

import numpy as np
import pytest
from sqlalchemy import select

from app.cli.seed_vetores import SeedVetoresError, seed_vetores
from app.models.politico import Politico


def _escrever_csv(caminho, cabecalho, linhas):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(linhas)


def _escrever_artefatos(tmp_path, linhas, com_clusters=True, dim=768):
    """linhas: list[(municipio, nome)]. Gera embeddings.npy + meta [+ clusters.csv]."""
    _escrever_csv(tmp_path / "embeddings_meta.csv", ["nome", "municipio"],
                  [(n, m) for (m, n) in linhas])
    emb = np.random.RandomState(0).randn(len(linhas), dim).astype("float32")
    np.save(tmp_path / "embeddings.npy", emb)
    if com_clusters:
        _escrever_csv(tmp_path / "clusters.csv", ["nome", "municipio", "cluster_id"],
                      [(n, m, i % 3) for i, (m, n) in enumerate(linhas)])
    return emb


def _add_politicos(db, linhas):
    for (m, n) in linhas:
        db.add(Politico(nome=n, municipio=m))
    db.commit()


def test_popula_embedding_e_cluster(tmp_path, db):
    linhas = [("JP", "Ana"), ("CG", "Bia")]
    _add_politicos(db, linhas)
    emb = _escrever_artefatos(tmp_path, linhas)

    resumo = seed_vetores(tmp_path, db)

    assert resumo["atualizados"] == 2
    assert resumo["com_embedding"] == 2
    assert resumo["sem_embedding"] == 0
    p = db.scalar(select(Politico).where(Politico.nome == "Ana"))
    assert p.embedding is not None
    assert len(p.embedding) == 768
    assert p.cluster_id == 0
    # o vetor gravado bate com a linha 0 de embeddings.npy
    assert np.allclose(np.asarray(p.embedding, dtype="float32"), emb[0], atol=1e-5)


def test_politicos_extra_ficam_null(tmp_path, db):
    # 3 políticos no banco, meta cobre só 2 → 1 fica sem embedding, SEM abortar (por design)
    _add_politicos(db, [("JP", "Ana"), ("CG", "Bia"), ("Patos", "Caio")])
    _escrever_artefatos(tmp_path, [("JP", "Ana"), ("CG", "Bia")])

    resumo = seed_vetores(tmp_path, db)

    assert resumo["com_embedding"] == 2
    assert resumo["sem_embedding"] == 1
    caio = db.scalar(select(Politico).where(Politico.nome == "Caio"))
    assert caio.embedding is None


def test_aborta_se_vereador_sem_politico(tmp_path, db):
    # meta tem um vereador (Zed) sem político correspondente → aborta, nada persiste
    _add_politicos(db, [("JP", "Ana")])
    _escrever_artefatos(tmp_path, [("JP", "Ana"), ("JP", "Zed")])

    with pytest.raises(SeedVetoresError):
        seed_vetores(tmp_path, db)

    # rollback: Ana NÃO recebeu embedding
    ana = db.scalar(select(Politico).where(Politico.nome == "Ana"))
    assert ana.embedding is None


def test_idempotente(tmp_path, db):
    linhas = [("JP", "Ana"), ("CG", "Bia")]
    _add_politicos(db, linhas)
    _escrever_artefatos(tmp_path, linhas)

    r1 = seed_vetores(tmp_path, db)
    r2 = seed_vetores(tmp_path, db)
    assert r1["com_embedding"] == r2["com_embedding"] == 2


def test_chave_normaliza_espacos(tmp_path, db):
    # político no banco com espaços extras; meta sem espaços → casa por strip
    _add_politicos(db, [("JP", "  Ana Silva  ")])
    _escrever_artefatos(tmp_path, [("JP", "Ana Silva")])

    resumo = seed_vetores(tmp_path, db)
    assert resumo["atualizados"] == 1
