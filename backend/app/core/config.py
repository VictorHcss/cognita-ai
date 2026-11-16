from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["fake", "gemini", "openai", "groq", "ollama"]


class Settings(BaseSettings):
    """Configuração carregada de variáveis de ambiente / arquivo .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cognita AI"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str = "postgresql+psycopg://cognita:cognita@localhost:5432/cognita"

    # Armazenamento dos arquivos originais: "local" (pasta no disco) ou "supabase"
    storage_backend: Literal["local", "supabase"] = "local"
    local_storage_dir: str = "data/uploads"
    max_upload_mb: int = 25

    # Chunking (em caracteres; ~4 caracteres ≈ 1 token)
    chunk_size: int = 1000
    chunk_overlap: int = 150

    supabase_url: str = ""
    supabase_service_key: SecretStr = SecretStr("")
    supabase_bucket: str = "documents"

    llm_provider: ProviderName = "fake"
    llm_model: str = ""  # vazio = padrão do provedor (Gemini: gemini-3.5-flash-lite)
    llm_temperature: float = 0.2  # baixa: respostas fiéis às fontes, pouca "criatividade"
    llm_max_tokens: int = 1024
    llm_thinking_level: str = ""  # vazio = padrão do modelo; ex.: "minimal", "low"

    # RAG: quantos trechos entram no contexto e similaridade mínima para usá-los
    rag_top_k: int = 5
    rag_min_score: float | None = None  # vazio = sem filtro; ex.: 0.55

    @field_validator("rag_min_score", mode="before")
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        # "RAG_MIN_SCORE=" no .env significa "sem filtro", não um número inválido.
        return None if isinstance(value, str) and not value.strip() else value

    embedding_provider: ProviderName = "fake"
    embedding_model: str = ""
    embedding_dimensions: int = 768

    gemini_api_key: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")
    groq_api_key: SecretStr = SecretStr("")
    ollama_base_url: str = "http://localhost:11434"


@lru_cache
def get_settings() -> Settings:
    return Settings()
