import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import DbDep
from app.providers.base import EmbeddingProvider
from app.providers.registry import get_embedding_provider
from app.services import retrieval

router = APIRouter(tags=["busca"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=retrieval.MAX_TOP_K)
    collection_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    min_score: float | None = Field(default=None, ge=-1, le=1)
    ef_search: int = Field(default=100, ge=10, le=1000)


class SearchResultOut(BaseModel):
    rank: int
    score: float
    chunk_id: int
    chunk_index: int
    document_id: uuid.UUID
    filename: str
    collection_id: uuid.UUID | None
    page_start: int
    page_end: int
    text: str


class SearchResponseOut(BaseModel):
    query: str
    embedding_model: str
    results: list[SearchResultOut]
    embed_ms: float
    search_ms: float
    warnings: list[str]


@router.post("/search", response_model=SearchResponseOut)
def search(
    payload: SearchRequest,
    db: DbDep,
    embedder: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> retrieval.SearchResponse:
    try:
        return retrieval.search(
            db,
            embedder,
            payload.query,
            top_k=payload.top_k,
            filters=retrieval.SearchFilters(payload.collection_id, payload.document_id),
            min_score=payload.min_score,
            ef_search=payload.ef_search,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
