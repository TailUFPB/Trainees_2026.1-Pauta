from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers import politicos, problemas, recomendacoes, usuarios, notificacoes

settings = get_settings()

app = FastAPI(
    title="Pauta API",
    version="0.1.0",
    description=(
        "Espinha dorsal do Pauta: problemas de infraestrutura (geo/PostGIS), "
        "recomendação de políticos (pgvector) e produção de eventos para notificações."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problemas.router)
app.include_router(recomendacoes.router)
app.include_router(usuarios.router)
app.include_router(politicos.router)
app.include_router(notificacoes.router)


# Serve as fotos salvas localmente no fallback de dev (sem Supabase Storage).
_uploads = Path("uploads")
_uploads.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads), name="uploads")


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok"}

