from functools import lru_cache

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
    # Segredo usado pra validar o JWT emitido pelo Supabase Auth.
    supabase_jwt_secret: str = "dev-insecure-secret-change-me"
    supabase_storage_bucket: str = "problemas"

    # Chave secreta para HMAC do autor em problemas (32+ bytes aleatórios).
    # Mudar essa chave invalida o vínculo dos reportes existentes — não
    # rotacionar sem plano. Gere com: secrets.token_urlsafe(32).
    autor_hmac_key: str

    # Dimensão do embedding — DEVE bater com o modelo do colega da recomendação.
    # Gemini text-embedding-004 = 768; OpenAI text-embedding-3-small = 1536.
    embedding_dim: int = 768

    # Regras de negócio do fluxo de problemas.
    confianca_minima_revisao: float = 0.6
    max_upload_bytes: int = 8 * 1024 * 1024  # 8 MB
    resolucao_minima_px: int = 256

    # CORS — origens do front em dev.
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
