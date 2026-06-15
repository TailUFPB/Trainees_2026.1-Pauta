import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers import (
    feed,
    notificacoes,
    politicos,
    problemas,
    publicacoes,
    recomendacoes,
    usuarios,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Aquece o modelo de embedding no startup (evita cold start no 1º request).

    Desligável via EMBEDDING_WARMUP (default False em dev/test, para não baixar o BERT).
    Falhas de warm-up (dep opcional ausente ou centróide faltando) NÃO derrubam o boot —
    o 1º request pagará o custo, ou retornará erro claro se faltar o asset.
    """
    if settings.embedding_warmup:
        try:
            from app.services.recomendacao import warmup

            warmup()
        except Exception as exc:  # noqa: BLE001 - warm-up é best-effort
            logging.getLogger("uvicorn.error").warning(
                "Warm-up de embedding pulado: %s", exc
            )
    yield


app = FastAPI(
    title="Pauta API",
    version="0.1.0",
    description=(
        "Espinha dorsal do Pauta: problemas de infraestrutura (geo/PostGIS), "
        "recomendação de políticos (pgvector) e produção de eventos para notificações."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(problemas.router)
app.include_router(publicacoes.router)
app.include_router(recomendacoes.router)
app.include_router(usuarios.router)
app.include_router(politicos.router)
app.include_router(notificacoes.router)
app.include_router(feed.router)

# Serve as fotos salvas localmente no fallback de dev (sem Supabase Storage).
_uploads = Path("uploads")
_uploads.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads), name="uploads")


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok"}

