"""Busca vetorial + filtro: o que o Postgres faz de verdade.

O planner escolhe entre duas estratégias:
1. **Filtro seletivo** (coleção pequena): usa índices comuns para achar os poucos chunks
   da coleção e calcula a distância EXATA de cada um. O HNSW nem é usado.
2. **HNSW** (filtro amplo ou sem filtro): percorre o índice aproximado e só depois aplica
   o filtro. Com uma janela pequena (`ef_search`), quase todos os vizinhos podem ser de
   outra coleção e o resultado fica menor que `top_k`. O `hnsw.iterative_scan`
   (pgvector ≥ 0.8) continua a busca até completar.
"""

import uuid

import pytest
from sqlalchemy import text

from app.db.models import EMBEDDING_DIM, Chunk, Collection, Document, DocumentStatus
from app.providers.fake import FakeEmbeddingProvider
from app.services import retrieval

EMBEDDER = FakeEmbeddingProvider(dimensions=EMBEDDING_DIM)


@pytest.fixture
def seeded(session_factory):
    """1000 chunks na coleção 'grande' e 5 na 'pequena'."""
    model = retrieval.model_id(EMBEDDER)
    with session_factory() as db:
        ids = {}
        for name, n in {"grande": 1000, "pequena": 5}.items():
            col = Collection(name=name)
            doc = Document(
                id=uuid.uuid4(),
                collection=col,
                filename=f"{name}.txt",
                file_type="txt",
                size_bytes=1,
                sha256=uuid.uuid4().hex,
                storage_key="x",
                status=DocumentStatus.PROCESSED,
            )
            db.add(doc)
            for i in range(n):
                t = f"{name} trecho {i}"
                db.add(
                    Chunk(
                        document=doc,
                        chunk_index=i,
                        text=t,
                        page_start=1,
                        page_end=1,
                        char_start=0,
                        char_end=len(t),
                        token_estimate=1,
                        embedding_model=model,
                        embedding=EMBEDDER._vector(t),
                    )
                )
            db.flush()
            ids[name] = col.id
        db.commit()
        db.execute(text("ANALYZE chunks"))
        db.execute(text("ANALYZE documents"))
        db.commit()
    return ids


def _search_small_collection(db, collection_id) -> list[str]:
    response = retrieval.search(
        db,
        EMBEDDER,
        "uma pergunta qualquer",
        top_k=5,
        filters=retrieval.SearchFilters(collection_id=collection_id),
        ef_search=10,
    )
    return [r.filename for r in response.results]


def _force_hnsw(db) -> None:
    # DDL é transacional no Postgres: retrieval.search faz rollback no fim e os índices voltam.
    db.execute(text("DROP INDEX ix_chunks_document_id"))
    db.execute(text("DROP INDEX ix_documents_collection_id"))
    db.execute(text("SET LOCAL enable_seqscan = off"))


def test_selective_filter_uses_exact_search(session_factory, seeded) -> None:
    with session_factory() as db:
        assert _search_small_collection(db, seeded["pequena"]) == ["pequena.txt"] * 5


def test_hnsw_with_filter_fills_top_k_thanks_to_iterative_scan(session_factory, seeded) -> None:
    with session_factory() as db:
        _force_hnsw(db)
        assert _search_small_collection(db, seeded["pequena"]) == ["pequena.txt"] * 5


def test_without_iterative_scan_hnsw_loses_filtered_results(
    session_factory, seeded, monkeypatch
) -> None:
    # Simula pgvector < 0.8: demonstra o problema que o iterative_scan resolve.
    monkeypatch.setattr(retrieval, "_pgvector_version", lambda db: (0, 7))
    with session_factory() as db:
        _force_hnsw(db)
        assert len(_search_small_collection(db, seeded["pequena"])) < 5


def test_indexes_are_restored_after_search(session_factory, seeded) -> None:
    with session_factory() as db:
        _force_hnsw(db)
        _search_small_collection(db, seeded["pequena"])
        names = set(db.scalars(text("SELECT indexname FROM pg_indexes")).all())
    assert {"ix_chunks_document_id", "ix_documents_collection_id"} <= names
