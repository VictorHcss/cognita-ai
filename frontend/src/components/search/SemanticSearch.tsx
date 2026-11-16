"use client";

import { Clock, FileText, Loader2, Search, SearchX, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Alert, Badge, Button, Card, CardHeader, EmptyState, fieldClasses } from "@/components/ui";
import {
  ApiError,
  type Collection,
  listCollections,
  searchChunks,
  type SearchResponse,
} from "@/lib/api";
import { cn } from "@/lib/cn";

const TOP_K_OPTIONS = [3, 5, 10, 20];

function pageLabel(start: number, end: number) {
  return start === end ? `p. ${start}` : `p. ${start}–${end}`;
}

/** Barra de similaridade em Cyan — a cor dos "elementos de inteligência". */
function ScoreBar({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score * 100));
  return (
    <div
      className="flex items-center gap-2"
      title={`Similaridade de cosseno: ${score.toFixed(4)}`}
    >
      <div
        className="h-1.5 w-20 overflow-hidden rounded-full bg-surface-2"
        role="meter"
        aria-label="Similaridade"
        aria-valuemin={0}
        aria-valuemax={1}
        aria-valuenow={Number(score.toFixed(3))}
      >
        <div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-xs text-accent-text tabular-nums">{score.toFixed(3)}</span>
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
      <Card className="p-4">
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="relative min-w-0 flex-1">
              <Search
                className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted"
                aria-hidden
              />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Faça uma pergunta sobre seus documentos…"
                maxLength={2000}
                aria-label="Pergunta"
                className={cn(fieldClasses, "w-full pl-9")}
              />
            </div>
            <Button
              type="submit"
              icon={loading ? Loader2 : Sparkles}
              disabled={loading || !query.trim()}
              className={cn(loading && "[&>svg]:animate-spin")}
            >
              {loading ? "Buscando…" : "Buscar"}
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted">
            <label className="flex items-center gap-2">
              Coleção
              <select
                value={collectionId}
                onChange={(e) => setCollectionId(e.target.value)}
                className={cn(fieldClasses, "h-8 pr-8 text-sm")}
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
                className={cn(fieldClasses, "h-8 pr-8 text-sm")}
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
      </Card>

      {error && <Alert>{error}</Alert>}

      {response && (
        <section className="animate-fade-in space-y-3" aria-live="polite">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
            <span className="font-medium text-text">
              {response.results.length} resultado(s)
            </span>
            <Badge tone="accent">
              <span className="font-mono">{response.embedding_model}</span>
            </Badge>
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3.5" aria-hidden />
              embedding {Math.round(response.embed_ms)} ms · busca{" "}
              {Math.round(response.search_ms)} ms
            </span>
          </div>
          {response.warnings.map((w) => (
            <Alert key={w} tone="warning">
              {w}
            </Alert>
          ))}
          {response.results.length === 0 && response.warnings.length === 0 && (
            <EmptyState icon={SearchX} title="Nenhum trecho encontrado">
              Envie documentos na Biblioteca ou tente outra pergunta.
            </EmptyState>
          )}
          <ol className="space-y-3">
            {response.results.map((r) => (
              <li key={r.chunk_id}>
                <Card className="transition hover:border-border-strong">
                  <CardHeader className="justify-between">
                    <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
                      <span className="font-mono font-medium text-text">#{r.rank}</span>
                      <Link
                        href={`/biblioteca/${r.document_id}?view=chunks`}
                        className="inline-flex min-w-0 items-center gap-1.5 font-medium text-link hover:underline"
                      >
                        <FileText className="size-3.5 shrink-0" aria-hidden />
                        <span className="truncate">{r.filename}</span>
                      </Link>
                      <Badge tone="info">{pageLabel(r.page_start, r.page_end)}</Badge>
                      <span>chunk {r.chunk_index}</span>
                    </div>
                    <ScoreBar score={r.score} />
                  </CardHeader>
                  <p className="px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap text-text">
                    {r.text}
                  </p>
                </Card>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}
