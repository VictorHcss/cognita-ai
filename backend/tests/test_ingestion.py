"""Pipeline completo: upload → páginas → chunks → embeddings no pgvector."""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import documents as documents_api
from app.db.models import EMBEDDING_DIM, Chunk
from app.providers.base import ProviderError
from tests.factories import make_pdf


def _upload(client: TestClient, name: str, data: bytes):
    return client.post("/api/documents", files={"file": (name, data)})


def test_pdf_is_chunked_and_embedded(client: TestClient, session_factory) -> None:
    pages = [f"Pagina {n}. " + "Texto sobre RAG e embeddings. " * 3 for n in (1, 2, 3)]
    doc_id = _upload(client, "rag.pdf", make_pdf(pages)).json()["id"]

    doc = client.get(f"/api/documents/{doc_id}").json()
    assert doc["status"] == "processed"
    assert doc["chunk_count"] >= 1

    chunks = client.get(f"/api/documents/{doc_id}/chunks").json()
    assert len(chunks) == doc["chunk_count"]
    assert chunks[0]["page_start"] == 1
    assert chunks[-1]["page_end"] == 3
    assert chunks[0]["embedding_model"] == "fake/fake-hash"

    with session_factory() as db:
        stored = db.scalars(select(Chunk).where(Chunk.document_id == doc_id)).all()
        assert all(len(c.embedding) == EMBEDDING_DIM for c in stored)


def test_long_document_produces_multiple_chunks(client: TestClient) -> None:
    text = "\n\n".join(f"Parágrafo {i}. " + "Conteúdo de estudo. " * 20 for i in range(30))
    doc_id = _upload(client, "longo.md", text.encode()).json()["id"]
    chunks = client.get(f"/api/documents/{doc_id}/chunks").json()
    assert len(chunks) > 5
    assert all(len(c["text"]) <= 1000 for c in chunks)
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_reprocess_replaces_chunks(client: TestClient) -> None:
    doc_id = _upload(client, "a.md", b"# Titulo\n\nConteudo.").json()["id"]
    before = client.get(f"/api/documents/{doc_id}/chunks").json()
    client.post(f"/api/documents/{doc_id}/reprocess")
    after = client.get(f"/api/documents/{doc_id}/chunks").json()
    assert len(after) == len(before) == 1


def test_embedding_failure_keeps_pages_and_explains(client: TestClient, monkeypatch) -> None:
    class BrokenEmbedder:
        name, model, dimensions = "broken", "x", EMBEDDING_DIM

        async def embed(self, texts, task="document"):
            raise ProviderError("cota excedida")

    monkeypatch.setattr(documents_api, "get_embedding_provider", lambda: BrokenEmbedder())
    doc_id = _upload(client, "b.txt", b"algum conteudo").json()["id"]

    doc = client.get(f"/api/documents/{doc_id}").json()
    assert doc["status"] == "failed"
    assert "cota excedida" in doc["error"]
    assert doc["page_count"] == 1
    assert client.get(f"/api/documents/{doc_id}/chunks").json() == []


def test_missing_provider_config_marks_failed(client: TestClient, monkeypatch) -> None:
    def no_key():
        raise ProviderError("GEMINI_API_KEY não configurada")

    monkeypatch.setattr(documents_api, "get_embedding_provider", no_key)
    doc_id = _upload(client, "c.txt", b"conteudo").json()["id"]
    doc = client.get(f"/api/documents/{doc_id}").json()
    assert doc["status"] == "failed"
    assert "GEMINI_API_KEY" in doc["error"]


def test_dimension_mismatch_is_reported(client: TestClient, monkeypatch) -> None:
    from app.providers.fake import FakeEmbeddingProvider

    monkeypatch.setattr(
        documents_api, "get_embedding_provider", lambda: FakeEmbeddingProvider(dimensions=1536)
    )
    doc_id = _upload(client, "d.txt", b"conteudo").json()["id"]
    assert "EMBEDDING_DIMENSIONS" in client.get(f"/api/documents/{doc_id}").json()["error"]
