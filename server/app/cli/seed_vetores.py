"""CLI re-executável que popula politicos.embedding e politicos.cluster_id a partir dos
artefatos do pipeline offline (recommendation/models/).

Diferente de seed_politicos.py (que cria/atualiza o PERFIL a partir de df_perfil.csv via
upsert), este faz um UPDATE determinístico nos políticos JÁ existentes, casando por
(municipio, nome) normalizado com:
  - embeddings.npy        (N, 768)  — vetor-perfil de cada vereador (ordem == meta)
  - embeddings_meta.csv   (nome, municipio) — na MESMA ordem de embeddings.npy
  - clusters.csv          (nome, municipio, cluster_id)

GARANTIA DE INTEGRIDADE (elimina o risco de mismatch de chave): se QUALQUER linha de
embeddings_meta não casar com um político no banco, a transação é ABORTADA (rollback) e
nada é persistido. Ou popula os N esperados, ou falha alto — nunca deixa o banco
meio-populado em silêncio. Os políticos sem embedding (ex.: perfis sem propostas) ficam
com embedding NULL e são excluídos da recomendação por design.

Uso: uv run python -m app.cli.seed_vetores [dir_artefatos]
     (default: <repo>/recommendation/models)
"""
import csv
import sys
from pathlib import Path

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.politico import Politico

# Diretório padrão dos artefatos: <repo>/recommendation/models
# seed_vetores.py = server/app/cli/seed_vetores.py -> parents[3] = <repo>
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODELS_DIR = REPO_ROOT / "recommendation" / "models"


class SeedVetoresError(RuntimeError):
    """Erro de integridade no seed de vetores (aborta sem persistir)."""


def _norm(valor: str | None) -> str:
    """Normaliza a chave de join — alinhado ao _normalizar de seed_politicos (strip)."""
    return (valor or "").strip()


def _ler_csv(caminho: Path) -> list[dict]:
    """Lê um CSV como lista de dicts (sem pandas — backend não depende dele)."""
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def seed_vetores(models_dir: Path, db: Session) -> dict:
    emb_path = models_dir / "embeddings.npy"
    meta_path = models_dir / "embeddings_meta.csv"
    clusters_path = models_dir / "clusters.csv"

    for p in (emb_path, meta_path):
        if not p.is_file():
            raise SeedVetoresError(f"Artefato obrigatório ausente: {p}")

    embeddings = np.load(emb_path)
    meta = _ler_csv(meta_path)
    if len(embeddings) != len(meta):
        raise SeedVetoresError(
            f"Desalinhamento: embeddings.npy={len(embeddings)} linhas, "
            f"embeddings_meta.csv={len(meta)}. Regenere o pipeline atomicamente."
        )

    # cluster_id por chave (opcional — clusters.csv pode não existir ainda)
    clusters_por_chave: dict[tuple[str, str], int] = {}
    if clusters_path.is_file():
        for r in _ler_csv(clusters_path):
            clusters_por_chave[(_norm(r["municipio"]), _norm(r["nome"]))] = int(r["cluster_id"])

    # índice dos políticos existentes por chave normalizada (municipio, nome)
    politicos = db.execute(select(Politico)).scalars().all()
    indice: dict[tuple[str, str], Politico] = {
        (_norm(p.municipio), _norm(p.nome)): p for p in politicos
    }

    atualizados = 0
    nao_encontrados: list[tuple[str, str]] = []
    com_cluster = 0

    for i, row in enumerate(meta):
        chave = (_norm(row["municipio"]), _norm(row["nome"]))
        politico = indice.get(chave)
        if politico is None:
            nao_encontrados.append(chave)
            continue
        politico.embedding = embeddings[i].astype(float).tolist()
        cid = clusters_por_chave.get(chave)
        if cid is not None:
            politico.cluster_id = cid
            com_cluster += 1
        atualizados += 1

    # ABORTA se qualquer vereador não casou — ou popula todos, ou nada.
    if nao_encontrados:
        db.rollback()
        amostra = ", ".join(f"{m}/{n}" for m, n in nao_encontrados[:5])
        raise SeedVetoresError(
            f"ABORTADO: {len(nao_encontrados)} de {len(meta)} vereadores sem político "
            f"correspondente no banco (ex.: {amostra}). Rode 'seed_politicos' antes e "
            "confirme que as chaves (municipio, nome) batem. Nada foi persistido."
        )

    db.commit()

    com_embedding = db.scalar(
        select(func.count()).select_from(Politico).where(Politico.embedding.isnot(None))
    ) or 0
    total = db.scalar(select(func.count()).select_from(Politico)) or 0
    return {
        "atualizados": atualizados,
        "com_cluster": com_cluster,
        "com_embedding": com_embedding,
        "total_politicos": total,
        "sem_embedding": total - com_embedding,
    }


def main(argv: list[str]) -> int:
    models_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_MODELS_DIR
    if not models_dir.is_dir():
        print(f"Diretório de artefatos não encontrado: {models_dir}", file=sys.stderr)
        return 1
    try:
        with SessionLocal() as db:
            resumo = seed_vetores(models_dir, db)
    except SeedVetoresError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        f"Vetores: {resumo['atualizados']} atualizados "
        f"({resumo['com_cluster']} c/ cluster) | "
        f"embedding populado em {resumo['com_embedding']}/{resumo['total_politicos']} "
        f"políticos ({resumo['sem_embedding']} sem embedding, NULL por design)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
