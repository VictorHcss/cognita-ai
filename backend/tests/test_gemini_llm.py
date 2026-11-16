"""Adaptador de geração do Gemini com API simulada."""

import asyncio
import json

import httpx
import pytest

from app.providers.base import ChatMessage, GenerationParams, ProviderError
from app.providers.gemini import GeminiLLMProvider


def _provider(handler) -> GeminiLLMProvider:
    return GeminiLLMProvider("chave", transport=httpx.MockTransport(handler))


def _ok(parts, finish="STOP", usage=None) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "candidates": [{"content": {"parts": parts}, "finishReason": finish}],
            "usageMetadata": usage or {"promptTokenCount": 10, "candidatesTokenCount": 3},
        },
    )


def test_builds_request_and_parses_response() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return _ok(
            [{"text": "raciocínio interno", "thought": True}, {"text": "Resposta [1]."}],
            usage={"promptTokenCount": 50, "candidatesTokenCount": 4, "thoughtsTokenCount": 30},
        )

    messages = [
        ChatMessage("system", "Regras"),
        ChatMessage("user", "Oi"),
        ChatMessage("assistant", "Olá"),
        ChatMessage("user", "Pergunta"),
    ]
    params = GenerationParams(temperature=0.1, max_tokens=256, thinking_level="minimal")
    result = asyncio.run(_provider(handler).generate(messages, params))

    body = seen["body"]
    assert seen["path"].endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert body["systemInstruction"] == {"parts": [{"text": "Regras"}]}
    assert [c["role"] for c in body["contents"]] == ["user", "model", "user"]
    assert body["generationConfig"]["maxOutputTokens"] == 256
    assert body["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "minimal"}

    assert result.text == "Resposta [1]."  # raciocínio fora da resposta
    assert result.usage.thinking_tokens == 30
    assert result.usage.total_tokens == 84
    assert result.finish_reason == "stop"


def test_no_thinking_config_by_default() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return _ok([{"text": "ok"}])

    asyncio.run(_provider(handler).generate([ChatMessage("user", "x")]))
    assert "thinkingConfig" not in seen["body"]["generationConfig"]
    assert "systemInstruction" not in seen["body"]


@pytest.mark.parametrize(("raw", "expected"), [("MAX_TOKENS", "length"), ("SAFETY", "safety")])
def test_finish_reasons(raw, expected) -> None:
    result = asyncio.run(
        _provider(lambda r: _ok([{"text": "parcial"}], finish=raw)).generate(
            [ChatMessage("user", "x")]
        )
    )
    assert result.finish_reason == expected


def test_blocked_prompt_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}})

    with pytest.raises(ProviderError, match="SAFETY"):
        asyncio.run(_provider(handler).generate([ChatMessage("user", "x")]))


def test_unavailable_model_error_is_clear() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"message": "model is no longer available"}})

    with pytest.raises(ProviderError, match="no longer available"):
        asyncio.run(_provider(handler).generate([ChatMessage("user", "x")]))
