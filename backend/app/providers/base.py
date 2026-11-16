"""Interfaces padronizadas para provedores de IA.

Os serviços (pipeline RAG, laboratórios) dependem apenas destas interfaces.
Cada provedor real (Gemini, OpenAI, Groq, Ollama) será um adaptador que as implementa.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant"]

# Alguns provedores (ex.: Gemini) geram vetores otimizados conforme o uso:
# "document" para os trechos indexados, "query" para a pergunta do usuário.
EmbeddingTask = Literal["document", "query"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class GenerationParams:
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 1.0
    # Modelos que "raciocinam" antes de responder (ex.: Gemini 3): None = padrão do modelo.
    # Raciocínio consome tokens de saída — com limite baixo, a resposta pode sair cortada.
    thinking_level: str | None = None


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    thinking_tokens: int = 0  # tokens de raciocínio (cobrados como saída)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens + self.thinking_tokens


# Por que a geração parou. "length" = atingiu o limite de tokens (resposta incompleta).
FinishReason = Literal["stop", "length", "safety", "other"]


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    finish_reason: FinishReason = "stop"


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

    async def embed(
        self, texts: list[str], task: EmbeddingTask = "document"
    ) -> list[list[float]]: ...


class ProviderError(RuntimeError):
    """Falha ao chamar um provedor externo (rede, cota, chave inválida...)."""
