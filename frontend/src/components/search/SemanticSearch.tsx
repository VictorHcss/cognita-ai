"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ApiError,
  type Collection,
  listCollections,
  searchChunks,
  type SearchResponse,
} from "@/lib/api";

const TOP_K_OPTIONS = [3, 5, 10, 20];

function pageLabel(start: number, end: number) {
  return start === end ? `p. ${start}` : `p. ${start}–${end}`;
}

function ScoreBar({ score }: { score: number }) {
  // Similaridade de cosseno típica de embeddings fica entre ~0,3 e ~0,9.
  const pct = Math.max(0, Math.min(100, score * 100));
  return (
    <div className="flex items-center gap-2" title={`Similaridade de cosseno: ${score.toFixed(4)}`}>
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-800">
        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-xs tabular-nums">{score.toFixed(3)}</span>
    </div>
  );
}

export function SemanticSearch() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [query, setQuery] = useState("");
  const [collectionId, setCollectionId] = useState("");
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  useEffect(() => {
    listCollections()
      .then(setCollections)
      .catch(() => setCollections([]));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      setResponse(
        await searchChunks({ query: q, top_k: topK, collection_id: collectionId || undefined }),
      );
    } catch (err) {
      setResponse(null);
      setError(
        err instanceof ApiError
          ? err.message
          : "Não foi possível falar com o backend. Ele está rodando?",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-3">
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Faça uma pergunta sobre seus documentos…"
            maxLength={2000}
            aria-label="Pergunta"
            className="min-w-0 flex-1 rounded-md border border-neutral-300 bg-transparent px-3 py-2 dark:border-neutral-700"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? "Buscando…" : "Buscar"}
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400">
          <label className="flex items-center gap-2">
            Coleção
            <select
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
              className="rounded-md border border-neutral-300 bg-transparent px-2 py-1 dark:border-neutral-700"
            >
              <option value="">Todas</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2">
            Resultados
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="rounded-md border border-neutral-300 bg-transparent px-2 py-1 dark:border-neutral-700"
            >
              {TOP_K_OPTIONS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </label>
        </div>
      </form>

      {error && (
        <p
          role="alert"
          className="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300"
        >
          {error}
        </p>
      )}

      {response && (
        <section className="space-y-3" aria-live="polite">
          <p className="text-xs text-neutral-500">
            {response.results.length} resultado(s) · modelo{" "}
            <code className="font-mono">{response.embedding_model}</code> · embedding{" "}
            {Math.round(response.embed_ms)} ms · busca {Math.round(response.search_ms)} ms
          </p>
          {response.warnings.map((w) => (
            <p
              key={w}
              className="rounded-md bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-300"
            >
              {w}
            </p>
          ))}
          {response.results.length === 0 && response.warnings.length === 0 && (
            <p className="py-6 text-center text-sm text-neutral-500">
              Nenhum trecho encontrado. Envie documentos na Biblioteca.
            </p>
          )}
          <ol className="space-y-3">
            {response.results.map((r) => (
              <li
                key={r.chunk_id}
                className="rounded-lg border border-neutral-200 dark:border-neutral-800"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-neutral-200 px-4 py-2 text-xs text-neutral-500 dark:border-neutral-800">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="font-medium text-neutral-700 dark:text-neutral-300">
                      #{r.rank}
                    </span>
                    <Link
                      href={`/biblioteca/${r.document_id}?view=chunks`}
                      className="font-medium text-indigo-600 hover:underline"
                    >
                      {r.filename}
                    </Link>
                    <span>{pageLabel(r.page_start, r.page_end)}</span>
                    <span>chunk {r.chunk_index}</span>
                  </div>
                  <ScoreBar score={r.score} />
                </div>
                <p className="px-4 py-3 text-sm whitespace-pre-wrap">{r.text}</p>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}
