"""Testa o adaptador Gemini com uma API simulada (sem rede e sem custo)."""

import asyncio
import json
import math

import httpx
import pytest

from app.providers.base import ProviderError
from app.providers.gemini import GeminiEmbeddingProvider


def _provider(handler, **kwargs) -> GeminiEmbeddingProvider:
    return GeminiEmbeddingProvider(
        "chave-de-teste", dimensions=4, transport=httpx.MockTransport(handler), **kwargs
    )


def test_sends_task_type_and_normalizes_vectors() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "chave-de-teste"
        assert request.url.path.endswith("/models/gemini-embedding-001:batchEmbedContents")
        body = json.loads(request.content)
        seen.append(body)
        return httpx.Response(
            200, json={"embeddings": [{"values": [3, 4, 0, 0]} for _ in body["requests"]]}
        )

    vectors = asyncio.run(_provider(handler).embed(["a", "b"], task="query"))
    req = seen[0]["requests"][0]
    assert req["taskType"] == "RETRIEVAL_QUERY"
    assert req["outputDimensionality"] == 4
    assert vectors[0] == [0.6, 0.8, 0.0, 0.0]
    assert math.isclose(sum(v * v for v in vectors[1]), 1.0)


def test_splits_into_batches_of_100() -> None:
    sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        n = len(json.loads(request.content)["requests"])
        sizes.append(n)
        return httpx.Response(200, json={"embeddings": [{"values": [1, 0, 0, 0]}] * n})

    vectors = asyncio.run(_provider(handler).embed([f"t{i}" for i in range(250)]))
    assert sizes == [100, 100, 50]
    assert len(vectors) == 250


def test_retries_on_rate_limit(monkeypatch) -> None:
    calls = {"n": 0}

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("app.providers.gemini.asyncio.sleep", no_sleep)

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, json={"error": {"message": "quota"}})
        return httpx.Response(200, json={"embeddings": [{"values": [0, 1, 0, 0]}]})

    assert asyncio.run(_provider(handler).embed(["x"])) == [[0.0, 1.0, 0.0, 0.0]]
    assert calls["n"] == 3


def test_reports_api_error_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"message": "API key not valid"}})

    with pytest.raises(ProviderError, match="API key not valid"):
        asyncio.run(_provider(handler).embed(["x"]))


def test_missing_key_is_a_clear_error() -> None:
    with pytest.raises(ProviderError, match="GEMINI_API_KEY"):
        GeminiEmbeddingProvider("")
