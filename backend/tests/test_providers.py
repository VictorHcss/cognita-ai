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


def test_fake_llm_cites_first_source_or_says_not_found() -> None:
    provider = build_llm_provider(Settings(_env_file=None))
    with_sources = "Fontes:\n\n[1] a.md — p. 1\ntexto\n\nPergunta: x"
    result = asyncio.run(provider.generate([ChatMessage("user", with_sources)]))
    assert result.text.endswith("[1].")
    assert result.usage.total_tokens > 0
    empty = asyncio.run(provider.generate([ChatMessage("user", "Pergunta sem fontes")]))
    assert empty.text == provider.NOT_FOUND


def test_unimplemented_provider_raises() -> None:
    with pytest.raises(ProviderNotAvailableError):
        build_llm_provider(Settings(_env_file=None, llm_provider="openai"))


def test_env_example_loads(monkeypatch) -> None:
    """O .env.example (com campos vazios) precisa carregar sem erro."""
    from pathlib import Path

    for line in Path(".env.example").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            monkeypatch.setenv(key, value)
    settings = Settings(_env_file=None)
    assert settings.rag_min_score is None
    assert settings.llm_thinking_level == ""
    assert settings.rag_top_k == 5
