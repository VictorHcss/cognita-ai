from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
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

    supabase_url: str = ""
    supabase_service_key: SecretStr = SecretStr("")
    supabase_bucket: str = "documents"

    llm_provider: ProviderName = "fake"
    llm_model: str = ""
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
