"""Avaliação da recuperação com um conjunto de perguntas e respostas esperadas.

Métricas (as mais usadas para avaliar busca em RAG):
- **hit@k**: em quantas perguntas o trecho certo apareceu entre os k primeiros.
  Se o chat usa os 5 primeiros chunks, hit@5 diz quantas vezes ele teve a informação.
- **MRR** (Mean Reciprocal Rank): média de 1/posição do primeiro acerto
  (1º lugar = 1; 2º = 0,5; 3º = 0,33; não achou = 0). Premia acertar no topo.

Um resultado é considerado relevante quando o texto do chunk contém o trecho esperado
(e, se informado, pertence ao documento esperado).
"""

import json
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from app.services.retrieval import SearchResponse


@dataclass(frozen=True)
class EvalCase:
    question: str
    expected: str  # trecho que precisa estar no chunk recuperado
    document: str | None = None  # nome do arquivo esperado (opcional)


@dataclass
class CaseResult:
    case: EvalCase
    rank: int | None  # posição do primeiro resultado relevante (1 = topo)
    top_score: float | None
    latency_ms: float


@dataclass
class EvalReport:
    ks: Sequence[int]
    cases: list[CaseResult] = field(default_factory=list)

    def hit_at(self, k: int) -> float:
        if not self.cases:
            return 0.0
        return sum(1 for c in self.cases if c.rank is not None and c.rank <= k) / len(self.cases)

    @property
    def mrr(self) -> float:
        if not self.cases:
            return 0.0
        return sum(1 / c.rank for c in self.cases if c.rank) / len(self.cases)

    @property
    def avg_latency_ms(self) -> float:
        return sum(c.latency_ms for c in self.cases) / len(self.cases) if self.cases else 0.0

    def summary(self) -> dict[str, float]:
        out = {f"hit@{k}": round(self.hit_at(k), 3) for k in self.ks}
        out["mrr"] = round(self.mrr, 3)
        out["latencia_media_ms"] = round(self.avg_latency_ms, 1)
        return out


def _norm(s: str) -> str:
    """Compara sem diferenciar maiúsculas, acentos e espaços extras."""
    s = unicodedata.normalize("NFKD", s.casefold())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.split())


def is_relevant(case: EvalCase, filename: str, chunk_text: str) -> bool:
    if case.document and filename != case.document:
        return False
    return _norm(case.expected) in _norm(chunk_text)


def evaluate(
    cases: Sequence[EvalCase],
    search_fn: Callable[[str], SearchResponse],
    ks: Sequence[int] = (1, 3, 5),
) -> EvalReport:
    report = EvalReport(ks=ks)
    for case in cases:
        response = search_fn(case.question)
        rank = next(
            (r.rank for r in response.results if is_relevant(case, r.filename, r.text)), None
        )
        report.cases.append(
            CaseResult(
                case=case,
                rank=rank,
                top_score=response.results[0].score if response.results else None,
                latency_ms=response.embed_ms + response.search_ms,
            )
        )
    return report


def load_cases(path: str | Path) -> list[EvalCase]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [EvalCase(**item) for item in data["cases"]]
