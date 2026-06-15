from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação, carregada de variáveis de ambiente / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco (Postgres com PostGIS + pgvector). Em prod aponta pro Supabase.
    database_url: str = "postgresql+psycopg://pauta:pauta@localhost:5432/pauta"

    # Supabase (Auth + Storage). Vazio em dev local sem Supabase.
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    supabase_storage_bucket: str = "problemas"

    # Chave simétrica do pgp_sym_encrypt para autor_cifrado (32+ bytes).
    # Será obrigatória após a Task 4 (Fatia 2); por ora aceita default vazio
    # pra não quebrar ambientes em transição. Gere com: secrets.token_urlsafe(32).
    autor_cifra_key: str = Field(
        default="",
        description="Chave simétrica do pgp_sym_encrypt para autor_cifrado (32+ bytes).",
    )
    # Chave HMAC do autor_lookup (32+ bytes, distinta de autor_cifra_key).
    # Mantém a busca por sub do autor sem expor o autor_cifrado em claro.
    autor_lookup_key: str = Field(
        default="",
        description="Chave HMAC do autor_lookup (32+ bytes, distinta de autor_cifra_key).",
    )

    # Dimensão do embedding — DEVE bater com o modelo da recomendação.
    # paraphrase-multilingual-mpnet-base-v2 (SBERT) = 768.
    embedding_dim: int = 768

    # Recomendação — modelo de embedding e centróide do corpus (pipeline offline).
    # MESMO modelo/centróide usados em recommendation/ para gerar os perfis dos políticos;
    # gerar_embedding projeta a query do cidadão neste mesmo espaço 768d.
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    # Caminho do centroid.npy (asset versionado, exportado de recommendation/models/).
    centroid_path: str = "app/assets/centroid.npy"
    # Evidências legislativas usadas para explicar cada match sem gerar texto por LLM.
    proposal_embeddings_path: str = "app/assets/proposal_embeddings.npy"
    proposal_embeddings_meta_path: str = "app/assets/proposal_embeddings_meta.csv"
    # Aquece o modelo no startup (evita cold start no 1º request). Em dev/test deixe
    # False para não baixar o BERT; em produção defina EMBEDDING_WARMUP=true.
    embedding_warmup: bool = False

    # LLM (Groq) p/ justificativas de recomendação em tempo real. Sem chave, o sistema
    # cai no texto-base (template de temas) — nada quebra.
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: float = 8.0

    # Regras de negócio do fluxo de problemas.
    confianca_minima_revisao: float = 0.6
    max_upload_bytes: int = 8 * 1024 * 1024  # 8 MB
    resolucao_minima_px: int = 256

    # CORS — origens do front em dev.
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
