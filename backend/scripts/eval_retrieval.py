"""Roda a avaliação de recuperação contra o banco e o provedor configurados no .env.

Uso (dentro de backend/):
    python -m scripts.eval_retrieval evaluation/datasets/temas.json
    python -m scripts.eval_retrieval evaluation/datasets/temas.json --top-k 3 --verbose
"""

import argparse
import json
import sys

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.evaluation.retrieval import evaluate, load_cases
from app.providers.registry import build_embedding_provider
from app.services import retrieval


def main() -> int:
    parser = argparse.ArgumentParser(description="Avalia a busca semântica (hit@k, MRR).")
    parser.add_argument("dataset", help="arquivo JSON com as perguntas")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--verbose", action="store_true", help="mostra cada pergunta")
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    embedder = build_embedding_provider(get_settings())
    ks = sorted({k for k in (1, 3, 5) if k <= args.top_k} | {args.top_k})

    with get_sessionmaker()() as db:

        def search_fn(question: str) -> retrieval.SearchResponse:
            return retrieval.search(db, embedder, question, top_k=args.top_k)

        report = evaluate(cases, search_fn, ks=ks)

    print(f"Modelo: {retrieval.model_id(embedder)} | perguntas: {len(cases)}\n")
    if args.verbose:
        for c in report.cases:
            pos = f"#{c.rank}" if c.rank else "não achou"
            score = f"{c.top_score:.3f}" if c.top_score is not None else "-"
            print(f"  [{pos:>9}] topo={score}  {c.case.question}")
        print()
    print(json.dumps(report.summary(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
