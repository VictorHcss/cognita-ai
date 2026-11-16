import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import DbDep, SettingsDep
from app.providers.base import EmbeddingProvider, GenerationParams, LLMProvider
from app.providers.registry import get_embedding_provider, get_llm_provider
from app.services import rag, retrieval

router = APIRouter(tags=["rag"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    collection_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    min_score: float | None = Field(default=None, ge=-1, le=1)


class SourceOut(BaseModel):
    number: int
    chunk_id: int
    chunk_index: int
    document_id: uuid.UUID
    filename: str
    page_start: int
    page_end: int
    score: float
    text: str
    cited: bool


class UsageOut(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    thinking_tokens: int
    total_tokens: int


class MessageOut(BaseModel):
    role: str
    content: str


class AskResponse(BaseModel):
    question: str
    answer: str
    grounded: bool
    not_found: bool
    cited: list[int]
    invalid_citations: list[int]
    sources: list[SourceOut]
    llm_provider: str
    llm_model: str
    embedding_model: str
    usage: UsageOut
    finish_reason: str | None
    timings: dict[str, float]
    messages: list[MessageOut]
    warnings: list[str]


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    db: DbDep,
    settings: SettingsDep,
    embedder: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> AskResponse:
    result = rag.answer_question(
        db,
        embedder,
        llm,
        payload.question,
        top_k=payload.top_k or settings.rag_top_k,
        filters=retrieval.SearchFilters(payload.collection_id, payload.document_id),
        min_score=payload.min_score if payload.min_score is not None else settings.rag_min_score,
        params=GenerationParams(
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            thinking_level=settings.llm_thinking_level or None,
        ),
    )
    return AskResponse(
        question=result.question,
        answer=result.answer,
        grounded=result.grounded,
        not_found=result.not_found,
        cited=result.cited,
        invalid_citations=result.invalid_citations,
        sources=[SourceOut(**vars(s)) for s in result.sources],
        llm_provider=result.llm_provider,
        llm_model=result.llm_model,
        embedding_model=result.embedding_model,
        usage=UsageOut(
            prompt_tokens=result.usage.prompt_tokens,
            completion_tokens=result.usage.completion_tokens,
            thinking_tokens=result.usage.thinking_tokens,
            total_tokens=result.usage.total_tokens,
        ),
        finish_reason=result.finish_reason,
        timings={k: round(v, 1) for k, v in result.timings.items()},
        messages=[MessageOut(role=m.role, content=m.content) for m in result.messages],
        warnings=result.warnings,
    )
