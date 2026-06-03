"""CLI re-executável que importa df_perfil.csv para a tabela politicos.

Uso: uv run python -m app.cli.seed_politicos <caminho/df_perfil.csv>
"""
import csv
import sys
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.politico import Politico


def _normalizar(valor: str | None, sentinel: str | None = None) -> str | None:
    if valor is None:
        return None
    v = valor.strip()
    if not v or v == sentinel:
        return None
    return v


def seed_from_csv(path: Path, db: Session) -> dict:
    importados = 0
    atualizados = 0
    with open(path, encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            values = dict(
                municipio=_normalizar(linha["municipio"]),
                nome=_normalizar(linha["nome"]),
                partido=_normalizar(linha["partido"], "sem_partido"),
                foto_url=_normalizar(linha["foto"]),
                fonte_url=_normalizar(linha["url_perfil"], "sem_perfil"),
            )
            stmt = insert(Politico).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["municipio", "nome"],
                set_=dict(
                    partido=stmt.excluded.partido,
                    foto_url=stmt.excluded.foto_url,
                    fonte_url=stmt.excluded.fonte_url,
                    updated_at=func.now(),
                ),
            ).returning(text("(xmax = 0) AS inserido"))
            inserido = db.execute(stmt).scalar()
            if inserido:
                importados += 1
            else:
                atualizados += 1
    db.commit()
    total = db.scalar(select(func.count()).select_from(Politico)) or 0
    return {"importados": importados, "atualizados": atualizados, "total": total}
