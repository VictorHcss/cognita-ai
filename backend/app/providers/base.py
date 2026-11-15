"""Interfaces padronizadas para provedores de IA.

Os serviços (pipeline RAG, laboratórios) dependem apenas destas interfaces.
Cada provedor real (Gemini, OpenAI, Groq, Ollama) será um adaptador que as implementa.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class GenerationParams:
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 1.0


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    model: str

    async def generate(
        self, messages: list[ChatMessage], params: GenerationParams | None = None
    ) -> LLMResult: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str
    model: str
    dimensions: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...
