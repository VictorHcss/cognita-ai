"""Embeddings do Gemini via API REST (Generative Language API).

Documentação: https://ai.google.dev/gemini-api/docs/embeddings
- Modelo padrão: gemini-embedding-001 (até 3072 dimensões; aceita reduzir para 768/1536).
- Ao reduzir as dimensões, o vetor deixa de vir normalizado — normalizamos aqui,
  para que similaridade de cosseno e produto interno fiquem equivalentes.
"""

import asyncio
import logging
import math
import time

import httpx

from app.providers.base import EmbeddingTask, ProviderError

logger = logging.getLogger("cognita.providers.gemini")

API_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
MAX_BATCH = 100  # limite de requisições por chamada batchEmbedContents
RETRY_STATUS = {429, 500, 502, 503, 504}

_TASK_TYPES: dict[EmbeddingTask, str] = {
    "document": "RETRIEVAL_DOCUMENT",
    "query": "RETRIEVAL_QUERY",
}


def _normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


class GeminiEmbeddingProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "",
        dimensions: int = 768,
        *,
        max_retries: int = 4,
        timeout: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ProviderError("GEMINI_API_KEY não configurada no backend/.env.")
        self.model = model or DEFAULT_EMBEDDING_MODEL
        self.dimensions = dimensions
        self._api_key = api_key
        self._max_retries = max_retries
        self._timeout = timeout
        self._transport = transport  # permite simular a API nos testes

    async def embed(self, texts: list[str], task: EmbeddingTask = "document") -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(
            base_url=API_URL,
            headers={"x-goog-api-key": self._api_key},
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            for i in range(0, len(texts), MAX_BATCH):
                vectors.extend(await self._batch(client, texts[i : i + MAX_BATCH], task))
        return vectors

    async def _batch(
        self, client: httpx.AsyncClient, texts: list[str], task: EmbeddingTask
    ) -> list[list[float]]:
        body = {
            "requests": [
                {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": t}]},
                    "taskType": _TASK_TYPES[task],
                    "outputDimensionality": self.dimensions,
                }
                for t in texts
            ]
        }
        url = f"/models/{self.model}:batchEmbedContents"
        start = time.perf_counter()
        for attempt in range(self._max_retries + 1):
            try:
                response = await client.post(url, json=body)
            except httpx.HTTPError as exc:
                if attempt == self._max_retries:
                    raise ProviderError(f"Gemini: falha de rede ({exc}).") from exc
                await asyncio.sleep(2**attempt)
                continue

            if response.status_code in RETRY_STATUS and attempt < self._max_retries:
                wait = float(response.headers.get("retry-after", 2**attempt))
                logger.warning(
                    "gemini_retry",
                    extra={"data": {"status": response.status_code, "wait_s": wait}},
                )
                await asyncio.sleep(wait)
                continue
            if response.is_error:
                raise ProviderError(f"Gemini {response.status_code}: {_error_message(response)}")

            embeddings = response.json().get("embeddings", [])
            if len(embeddings) != len(texts):
                raise ProviderError("Gemini devolveu um número inesperado de embeddings.")
            vectors = [_normalize(e["values"]) for e in embeddings]
            if any(len(v) != self.dimensions for v in vectors):
                raise ProviderError(
                    f"Gemini devolveu vetores com dimensão diferente de {self.dimensions}."
                )
            logger.info(
                "gemini_embed",
                extra={
                    "data": {
                        "model": self.model,
                        "texts": len(texts),
                        "chars": sum(len(t) for t in texts),
                        "ms": round((time.perf_counter() - start) * 1000, 1),
                    }
                },
            )
            return vectors
        raise ProviderError("Gemini: limite de tentativas excedido.")


def _error_message(response: httpx.Response) -> str:
    try:
        return response.json()["error"]["message"]
    except (ValueError, KeyError, TypeError):
        return response.text[:300]
