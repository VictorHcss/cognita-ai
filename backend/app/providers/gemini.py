"""Adaptadores do Gemini via API REST (Generative Language API).

Embeddings — https://ai.google.dev/gemini-api/docs/embeddings
- Modelo padrão: gemini-embedding-001 (até 3072 dimensões; aceita reduzir para 768/1536).
- Ao reduzir as dimensões, o vetor deixa de vir normalizado — normalizamos aqui.

Geração de texto — https://ai.google.dev/gemini-api/docs/text-generation
- Modelo padrão: gemini-3.5-flash-lite (rápido; modelos 2.5 não aceitam contas novas).
- Mensagens "system" viram `systemInstruction`; "assistant" vira o papel "model".
- Partes marcadas como `thought` são o raciocínio interno: ficam fora da resposta.
"""

import asyncio
import logging
import math
import time
from typing import Any

import httpx

from app.providers.base import (
    ChatMessage,
    EmbeddingTask,
    FinishReason,
    GenerationParams,
    LLMResult,
    ProviderError,
    TokenUsage,
)

logger = logging.getLogger("cognita.providers.gemini")

API_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_LLM_MODEL = "gemini-3.5-flash-lite"
MAX_BATCH = 100  # limite de requisições por chamada batchEmbedContents
RETRY_STATUS = {429, 500, 502, 503, 504}

_TASK_TYPES: dict[EmbeddingTask, str] = {
    "document": "RETRIEVAL_DOCUMENT",
    "query": "RETRIEVAL_QUERY",
}

_FINISH: dict[str, FinishReason] = {
    "STOP": "stop",
    "MAX_TOKENS": "length",
    "SAFETY": "safety",
    "RECITATION": "safety",
    "PROHIBITED_CONTENT": "safety",
    "BLOCKLIST": "safety",
}


def _normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def _error_message(response: httpx.Response) -> str:
    try:
        return response.json()["error"]["message"]
    except (ValueError, KeyError, TypeError):
        return response.text[:300]


class _GeminiClient:
    """Cliente HTTP com novas tentativas para erros temporários (cota, instabilidade)."""

    def __init__(
        self,
        api_key: str,
        *,
        max_retries: int,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None,
    ) -> None:
        if not api_key:
            raise ProviderError("GEMINI_API_KEY não configurada no backend/.env.")
        self._api_key = api_key
        self._max_retries = max_retries
        self._timeout = timeout
        self._transport = transport  # permite simular a API nos testes

    def session(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=API_URL,
            headers={"x-goog-api-key": self._api_key},
            timeout=self._timeout,
            transport=self._transport,
        )

    async def post(self, client: httpx.AsyncClient, url: str, body: dict[str, Any]) -> dict:
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
            return response.json()
        raise ProviderError("Gemini: limite de tentativas excedido.")


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
        self._client = _GeminiClient(
            api_key, max_retries=max_retries, timeout=timeout, transport=transport
        )
        self.model = model or DEFAULT_EMBEDDING_MODEL
        self.dimensions = dimensions

    async def embed(self, texts: list[str], task: EmbeddingTask = "document") -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        async with self._client.session() as client:
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
        start = time.perf_counter()
        data = await self._client.post(client, f"/models/{self.model}:batchEmbedContents", body)
        embeddings = data.get("embeddings", [])
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


class GeminiLLMProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "",
        *,
        max_retries: int = 3,
        timeout: float = 120.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = _GeminiClient(
            api_key, max_retries=max_retries, timeout=timeout, transport=transport
        )
        self.model = model or DEFAULT_LLM_MODEL

    @staticmethod
    def _body(messages: list[ChatMessage], params: GenerationParams) -> dict[str, Any]:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in messages
            if m.role != "system"
        ]
        config: dict[str, Any] = {
            "temperature": params.temperature,
            "maxOutputTokens": params.max_tokens,
            "topP": params.top_p,
        }
        if params.thinking_level:
            config["thinkingConfig"] = {"thinkingLevel": params.thinking_level}
        body: dict[str, Any] = {"contents": contents, "generationConfig": config}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        return body

    async def generate(
        self, messages: list[ChatMessage], params: GenerationParams | None = None
    ) -> LLMResult:
        params = params or GenerationParams()
        start = time.perf_counter()
        async with self._client.session() as client:
            data = await self._client.post(
                client, f"/models/{self.model}:generateContent", self._body(messages, params)
            )
        latency_ms = (time.perf_counter() - start) * 1000

        candidates = data.get("candidates") or []
        if not candidates:
            reason = (data.get("promptFeedback") or {}).get("blockReason", "sem resposta")
            raise ProviderError(f"Gemini não gerou resposta ({reason}).")
        candidate = candidates[0]
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        usage = data.get("usageMetadata") or {}
        result = LLMResult(
            text=text,
            provider=self.name,
            model=self.model,
            usage=TokenUsage(
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
                thinking_tokens=usage.get("thoughtsTokenCount", 0),
            ),
            latency_ms=latency_ms,
            finish_reason=_FINISH.get(candidate.get("finishReason", "STOP"), "other"),
        )
        logger.info(
            "gemini_generate",
            extra={
                "data": {
                    "model": self.model,
                    "prompt_tokens": result.usage.prompt_tokens,
                    "completion_tokens": result.usage.completion_tokens,
                    "thinking_tokens": result.usage.thinking_tokens,
                    "finish": result.finish_reason,
                    "ms": round(latency_ms, 1),
                }
            },
        )
        return result
