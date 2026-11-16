"""Provedores determinísticos para testes e desenvolvimento offline (sem rede, sem custo)."""

import hashlib
import math
import time

from app.providers.base import (
    ChatMessage,
    EmbeddingTask,
    GenerationParams,
    LLMResult,
    TokenUsage,
)


class FakeLLMProvider:
    name = "fake"

    def __init__(self, model: str = "fake-echo") -> None:
        self.model = model or "fake-echo"

    async def generate(
        self, messages: list[ChatMessage], params: GenerationParams | None = None
    ) -> LLMResult:
        start = time.perf_counter()
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        text = f"[fake] Você perguntou: {last_user}"
        prompt_tokens = sum(len(m.content.split()) for m in messages)
        return LLMResult(
            text=text,
            provider=self.name,
            model=self.model,
            usage=TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=len(text.split())),
            latency_ms=(time.perf_counter() - start) * 1000,
        )


class FakeEmbeddingProvider:
    """Gera vetores normalizados a partir do hash do texto: mesmo texto → mesmo vetor."""

    name = "fake"

    def __init__(self, model: str = "fake-hash", dimensions: int = 768) -> None:
        self.model = model or "fake-hash"
        self.dimensions = dimensions

    def _vector(self, text: str) -> list[float]:
        values: list[float] = []
        counter = 0
        while len(values) < self.dimensions:
            digest = hashlib.sha256(f"{counter}:{text}".encode()).digest()
            values.extend((b / 127.5) - 1.0 for b in digest)
            counter += 1
        values = values[: self.dimensions]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    async def embed(self, texts: list[str], task: EmbeddingTask = "document") -> list[list[float]]:
        return [self._vector(t) for t in texts]
