"""Busca semântica pela API.

O provedor fake gera o MESMO vetor para o MESMO texto: buscar exatamente o texto de um
chunk deve trazê-lo em 1º lugar com similaridade 1. Isso testa a mecânica (pgvector,
ordenação, filtros); a qualidade semântica real é medida com o Gemini na avaliação.
"""

from fastapi.testclient import TestClient

from app.db.models import EMBEDDING_DIM
from app.providers.fake import FakeEmbeddingProvider
from app.providers.registry import get_embedding_provider

TEXTS = {
    "risoto.md": "O risoto usa arroz arbóreo e caldo quente.",
    "estrelas.md": "Buracos negros surgem do colapso de estrelas massivas.",
    "copa.md": "O Brasil venceu a Copa do Mundo cinco vezes.",
}


def _seed(client: TestClient, collection_id: str | None = None) -> dict[str, str]:
    ids = {}
    for name, content in TEXTS.items():
        form = {"collection_id": collection_id} if collection_id else {}
        r = client.post("/api/documents", files={"file": (name, content.encode())}, data=form)
        ids[name] = r.json()["id"]
    return ids


def _search(client: TestClient, **payload):
    return client.post("/api/search", json=payload)


def test_exact_text_ranks_first_with_score_one(client: TestClient) -> None:
    _seed(client)
    body = _search(client, query=TEXTS["copa.md"], top_k=3).json()
    assert body["embedding_model"] == "fake/fake-hash"
    first = body["results"][0]
    assert first["filename"] == "copa.md"
    assert first["rank"] == 1
    assert abs(first["score"] - 1.0) < 1e-3
    assert (first["page_start"], first["page_end"]) == (1, 1)
    scores = [r["score"] for r in body["results"]]
    assert scores == sorted(scores, reverse=True)
    assert body["embed_ms"] >= 0 and body["search_ms"] >= 0


def test_top_k_limits_results(client: TestClient) -> None:
    _seed(client)
    assert len(_search(client, query="qualquer", top_k=2).json()["results"]) == 2


def test_filters_by_collection_and_document(client: TestClient) -> None:
    col = client.post("/api/collections", json={"name": "Esportes"}).json()["id"]
    r = client.post(
        "/api/documents",
        files={"file": ("futebol.md", b"Goleiros decidem disputas de penaltis.")},
        data={"collection_id": col},
    )
    ids = _seed(client)

    in_col = _search(client, query=TEXTS["risoto.md"], collection_id=col, top_k=10).json()
    assert [x["filename"] for x in in_col["results"]] == ["futebol.md"]

    in_doc = _search(client, query="x", document_id=ids["estrelas.md"], top_k=10).json()
    assert {x["filename"] for x in in_doc["results"]} == {"estrelas.md"}
    assert r.status_code == 201


def test_min_score_filters_weak_matches(client: TestClient) -> None:
    _seed(client)
    body = _search(client, query=TEXTS["risoto.md"], top_k=10, min_score=0.99).json()
    assert [x["filename"] for x in body["results"]] == ["risoto.md"]


def test_other_embedding_model_is_not_mixed(client: TestClient) -> None:
    _seed(client)  # indexado com fake/fake-hash

    class OtherModel(FakeEmbeddingProvider):
        name = "outro"

    from app.main import app

    app.dependency_overrides[get_embedding_provider] = lambda: OtherModel(dimensions=EMBEDDING_DIM)
    body = _search(client, query=TEXTS["copa.md"]).json()
    assert body["results"] == []
    assert "outro modelo" in body["warnings"][0]


def test_validation(client: TestClient) -> None:
    assert _search(client, query="").status_code == 422
    assert _search(client, query="   ").status_code == 422
    assert _search(client, query="ok", top_k=0).status_code == 422
    assert _search(client, query="ok").json()["results"] == []  # biblioteca vazia
