"""Seleciona o provedor configurado. Novos adaptadores são registrados aqui."""

from app.core.config import Settings
from app.providers.base import EmbeddingProvider, LLMProvider
from app.providers.fake import FakeEmbeddingProvider, FakeLLMProvider


class ProviderNotAvailableError(RuntimeError):
    pass


def build_llm_provider(settings: Settings) -> LLMProvider:
    match settings.llm_provider:
        case "fake":
            return FakeLLMProvider(settings.llm_model)
        case other:
            raise ProviderNotAvailableError(
                f"Provedor de LLM '{other}' ainda não implementado (previsto na Etapa 5/8)."
            )


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    match settings.embedding_provider:
        case "fake":
            return FakeEmbeddingProvider(settings.embedding_model, settings.embedding_dimensions)
        case other:
            raise ProviderNotAvailableError(
                f"Provedor de embeddings '{other}' ainda não implementado (previsto na Etapa 3)."
            )
