import asyncio
import math

import pytest

from app.core.config import Settings
from app.providers.base import ChatMessage, EmbeddingProvider, LLMProvider
from app.providers.registry import (
    ProviderNotAvailableError,
    build_embedding_provider,
    build_llm_provider,
)


def test_fake_providers_satisfy_interfaces() -> None:
    settings = Settings(_env_file=None)
    assert isinstance(build_llm_provider(settings), LLMProvider)
    assert isinstance(build_embedding_provider(settings), EmbeddingProvider)


def test_fake_embeddings_are_deterministic_and_normalized() -> None:
    provider = build_embedding_provider(Settings(_env_file=None, embedding_dimensions=64))
    a1, a2, b = asyncio.run(provider.embed(["olá mundo", "olá mundo", "outro texto"]))
    assert len(a1) == 64
    assert a1 == a2
    assert a1 != b
    assert math.isclose(math.sqrt(sum(v * v for v in a1)), 1.0, rel_tol=1e-9)


def test_fake_llm_reports_usage() -> None:
    provider = build_llm_provider(Settings(_env_file=None))
    result = asyncio.run(provider.generate([ChatMessage("user", "O que é RAG?")]))
    assert "O que é RAG?" in result.text
    assert result.usage.total_tokens > 0


def test_unimplemented_provider_raises() -> None:
    with pytest.raises(ProviderNotAvailableError):
        build_llm_provider(Settings(_env_file=None, llm_provider="openai"))
