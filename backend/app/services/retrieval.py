"""Busca semântica: pergunta → embedding → chunks mais próximos no pgvector.

Conceitos:
- **Similaridade de cosseno** = 1 − distância de cosseno (operador `<=>` do pgvector).
  Vai de −1 a 1; quanto maior, mais parecido o significado.
- **HNSW** é um índice *aproximado*: em troca de velocidade, pode deixar passar
  algum vizinho. `hnsw.ef_search` controla o equilíbrio (maior = mais preciso, mais lento).
- **Filtros + HNSW**: o índice encontra os vizinhos e só depois o filtro (coleção,
  documento) é aplicado — poderia sobrar menos do que `top_k`. Desde o pgvector 0.8,
  `hnsw.iterative_scan` continua buscando até completar o resultado.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.providers.base import EmbeddingProvider

logger = logging.getLogger("cognita.retrieval")

MAX_TOP_K = 50


@dataclass(frozen=True)
class SearchFilters:
    collection_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None


@dataclass(frozen=True)
class SearchResult:
    rank: int
    score: float  # similaridade de cosseno
    chunk_id: int
    chunk_index: int
    document_id: uuid.UUID
    filename: str
    collection_id: uuid.UUID | None
    page_start: int
    page_end: int
    text: str


@dataclass
class SearchResponse:
    query: str
    embedding_model: str
    results: list[SearchResult]
    embed_ms: float
    search_ms: float
    warnings: list[str] = field(default_factory=list)


def model_id(embedder: EmbeddingProvider) -> str:
    """Identificador gravado em cada chunk (ver Chunk.embedding_model)."""
    return f"{embedder.name}/{embedder.model}"


def _pgvector_version(db: Session) -> tuple[int, ...]:
    raw = db.scalar(text("select extversion from pg_extension where extname = 'vector'")) or "0"
    return tuple(int(p) for p in raw.split(".") if p.isdigit())


def _tune_hnsw(db: Session, ef_search: int) -> None:
    # SET não aceita parâmetros vinculados; ef_search já foi validado como inteiro.
    db.execute(text(f"SET LOCAL hnsw.ef_search = {int(ef_search)}"))
    if _pgvector_version(db) >= (0, 8):
        db.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))


def search(
    db: Session,
    embedder: EmbeddingProvider,
    query: str,
    *,
    top_k: int = 5,
    filters: SearchFilters = SearchFilters(),
    min_score: float | None = None,
    ef_search: int = 100,
) -> SearchResponse:
    query = query.strip()
    if not query:
        raise ValueError("A pergunta não pode ser vazia.")
    top_k = max(1, min(top_k, MAX_TOP_K))
    model = model_id(embedder)

    # 1. Embedding da pergunta (task="query": otimizado para buscar documentos)
    t0 = time.perf_counter()
    [query_vector] = asyncio.run(embedder.embed([query], task="query"))
    embed_ms = (time.perf_counter() - t0) * 1000

    # 2. Vizinhos mais próximos — só entre vetores do MESMO modelo
    t0 = time.perf_counter()
    distance = Chunk.embedding.cosine_distance(query_vector)
    stmt = (
        select(Chunk, Document.filename, Document.collection_id, distance.label("distance"))
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.embedding_model == model)
        .order_by(distance)
        .limit(top_k)
    )
    if filters.collection_id:
        stmt = stmt.where(Document.collection_id == filters.collection_id)
    if filters.document_id:
        stmt = stmt.where(Chunk.document_id == filters.document_id)

    _tune_hnsw(db, ef_search)
    rows = db.execute(stmt).all()
    search_ms = (time.perf_counter() - t0) * 1000

    # iterative_scan "relaxed_order" pode devolver fora de ordem: reordenamos aqui.
    scored = sorted(
        ((1.0 - float(dist), chunk, filename, coll) for chunk, filename, coll, dist in rows),
        key=lambda r: r[0],
        reverse=True,
    )
    if min_score is not None:
        scored = [r for r in scored if r[0] >= min_score]

    results = [
        SearchResult(
            rank=i + 1,
            score=round(score, 4),
            chunk_id=chunk.id,
            chunk_index=chunk.chunk_index,
            document_id=chunk.document_id,
            filename=filename,
            collection_id=coll,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            text=chunk.text,
        )
        for i, (score, chunk, filename, coll) in enumerate(scored)
    ]

    warnings: list[str] = []
    if not rows:
        other_models = db.scalar(select(func.count(Chunk.id)).where(Chunk.embedding_model != model))
        if other_models:
            warnings.append(
                f"{other_models} chunk(s) foram indexados com outro modelo de embedding e "
                f"não são comparáveis com '{model}'. Reprocesse os documentos."
            )
    db.rollback()  # encerra a transação e descarta os SET LOCAL

    logger.info(
        "search",
        extra={
            "data": {
                "model": model,
                "top_k": top_k,
                "results": len(results),
                "best": results[0].score if results else None,
                "embed_ms": round(embed_ms, 1),
                "search_ms": round(search_ms, 1),
            }
        },
    )
    return SearchResponse(query, model, results, embed_ms, search_ms, warnings)
