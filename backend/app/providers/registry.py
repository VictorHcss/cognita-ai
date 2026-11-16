"""Seleciona o provedor configurado. Novos adaptadores são registrados aqui."""

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.providers.base import EmbeddingProvider, LLMProvider, ProviderError
from app.providers.fake import FakeEmbeddingProvider, FakeLLMProvider


class ProviderNotAvailableError(ProviderError):
    pass


def build_llm_provider(settings: Settings) -> LLMProvider:
    match settings.llm_provider:
        case "fake":
            return FakeLLMProvider(settings.llm_model)
        case "gemini":
            from app.providers.gemini import GeminiLLMProvider

            return GeminiLLMProvider(settings.gemini_api_key.get_secret_value(), settings.llm_model)
        case other:
            raise ProviderNotAvailableError(
                f"Provedor de LLM '{other}' ainda não implementado (previsto na Etapa 8)."
            )


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    match settings.embedding_provider:
        case "fake":
            return FakeEmbeddingProvider(settings.embedding_model, settings.embedding_dimensions)
        case "gemini":
            from app.providers.gemini import GeminiEmbeddingProvider

            return GeminiEmbeddingProvider(
                settings.gemini_api_key.get_secret_value(),
                settings.embedding_model,
                settings.embedding_dimensions,
            )
        case other:
            raise ProviderNotAvailableError(
                f"Provedor de embeddings '{other}' ainda não implementado (previsto na Etapa 8)."
            )


def get_llm_provider() -> LLMProvider:
    """Dependência do FastAPI."""
    return _cached_llm_provider()


@lru_cache
def _cached_llm_provider() -> LLMProvider:
    return build_llm_provider(get_settings())


def get_embedding_provider() -> EmbeddingProvider:
    """Dependência do FastAPI."""
    return _cached_embedding_provider()


@lru_cache
def _cached_embedding_provider() -> EmbeddingProvider:
    return build_embedding_provider(get_settings())
