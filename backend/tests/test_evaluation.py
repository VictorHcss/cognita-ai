import uuid

import pytest

from app.evaluation.retrieval import EvalCase, evaluate, is_relevant
from app.services.retrieval import SearchResponse, SearchResult


def _result(rank: int, text: str, filename: str = "a.md") -> SearchResult:
    return SearchResult(
        rank=rank,
        score=1 - rank / 10,
        chunk_id=rank,
        chunk_index=rank,
        document_id=uuid.uuid4(),
        filename=filename,
        collection_id=None,
        page_start=1,
        page_end=1,
        text=text,
    )


def test_relevance_ignores_case_accents_and_spacing() -> None:
    case = EvalCase("?", "Seleção   BRASILEIRA")
    assert is_relevant(case, "x.md", "a selecao brasileira venceu")
    assert not is_relevant(EvalCase("?", "Brasil", document="y.md"), "x.md", "Brasil")


def test_hit_at_k_and_mrr() -> None:
    answers = {
        "q1": ["certo", "b", "c"],  # 1º lugar → 1
        "q2": ["a", "b", "certo"],  # 3º lugar → 1/3
        "q3": ["a", "b", "c"],  # não achou → 0
    }

    def search_fn(q: str) -> SearchResponse:
        results = [_result(i + 1, t) for i, t in enumerate(answers[q])]
        return SearchResponse(q, "fake", results, embed_ms=1.0, search_ms=2.0)

    report = evaluate([EvalCase(q, "certo") for q in answers], search_fn, ks=(1, 3))
    assert report.hit_at(1) == pytest.approx(1 / 3)
    assert report.hit_at(3) == pytest.approx(2 / 3)
    assert report.mrr == pytest.approx((1 + 1 / 3 + 0) / 3)
    assert report.summary()["latencia_media_ms"] == 3.0
