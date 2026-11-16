"use client";

import {
  BookOpenCheck,
  ChevronDown,
  CircleAlert,
  Clock,
  Coins,
  FileText,
  Loader2,
  MessageSquareText,
  SearchX,
  SendHorizontal,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Alert, Badge, Button, Card, CardHeader, fieldClasses } from "@/components/ui";
import {
  type AnswerSource,
  ApiError,
  askQuestion,
  type AskResponse,
  type Collection,
  listCollections,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import { AnswerText } from "./AnswerText";

const SUGGESTIONS = [
  "Quanto dinheiro devo guardar para imprevistos?",
  "Como a pergunta do usuário é usada num sistema RAG?",
  "Quantas vezes o Brasil ganhou a Copa?",
];

function pageLabel(start: number, end: number) {
  return start === end ? `p. ${start}` : `p. ${start}–${end}`;
}

function seconds(ms: number | undefined) {
  return ms === undefined ? "—" : `${(ms / 1000).toFixed(1)} s`;
}

function Verdict({ r }: { r: AskResponse }) {
  if (r.not_found)
    return (
      <Badge tone="neutral">
        <SearchX className="size-3.5" aria-hidden /> Não encontrado nas fontes
      </Badge>
    );
  if (r.grounded)
    return (
      <Badge tone="success">
        <BookOpenCheck className="size-3.5" aria-hidden /> Fundamentada em {r.cited.length} fonte(s)
      </Badge>
    );
  return (
    <Badge tone="warning">
      <CircleAlert className="size-3.5" aria-hidden /> Confira: citações ausentes ou inválidas
    </Badge>
  );
}

function SourceCard({ s, highlighted }: { s: AnswerSource; highlighted: boolean }) {
  return (
    <Card
      id={`fonte-${s.number}`}
      className={cn(
        "scroll-mt-24 transition",
        s.cited ? "border-accent/40" : "opacity-75",
        highlighted && "ring-2 ring-accent",
      )}
    >
      <details open={s.cited}>
        <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
          <CardHeader className="justify-between border-b-0">
            <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
              <span
                className={cn(
                  "flex size-6 items-center justify-center rounded font-mono text-xs font-semibold",
                  s.cited ? "bg-accent-soft text-accent-text" : "bg-surface-2 text-muted",
                )}
              >
                {s.number}
              </span>
              <Link
                href={`/biblioteca/${s.document_id}?view=chunks`}
                className="inline-flex min-w-0 items-center gap-1.5 font-medium text-link hover:underline"
              >
                <FileText className="size-3.5 shrink-0" aria-hidden />
                <span className="truncate">{s.filename}</span>
              </Link>
              <Badge tone="info">{pageLabel(s.page_start, s.page_end)}</Badge>
              {!s.cited && <span className="text-muted">não citada</span>}
            </div>
            <span className="flex items-center gap-2">
              <span
                className="font-mono text-xs text-accent-text tabular-nums"
                title="Similaridade de cosseno com a pergunta"
              >
                {s.score.toFixed(3)}
              </span>
              <ChevronDown className="size-4 text-muted" aria-hidden />
            </span>
          </CardHeader>
        </summary>
        <p className="border-t border-border px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap text-text">
          {s.text}
        </p>
      </details>
    </Card>
  );
}

export function AskPanel() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [collectionId, setCollectionId] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [highlight, setHighlight] = useState<number | null>(null);
  const answerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listCollections()
      .then(setCollections)
      .catch(() => setCollections([]));
  }, []);

  async function submit(q = question) {
    const text = q.trim();
    if (!text || loading) return;
    setQuestion(text);
    setLoading(true);
    setError(null);
    setHighlight(null);
    try {
      setResult(await askQuestion({ question: text, collection_id: collectionId || undefined }));
      requestAnimationFrame(() =>
        answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
      );
    } catch (err) {
      setResult(null);
      setError(
        err instanceof ApiError
          ? err.message
          : "Não foi possível falar com o backend. Ele está rodando?",
      );
    } finally {
      setLoading(false);
    }
  }

  function goToSource(n: number) {
    setHighlight(n);
    const el = document.getElementById(`fonte-${n}`);
    el?.querySelector("details")?.setAttribute("open", "");
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  const valid = new Set(result?.sources.map((s) => s.number));

  return (
    <div className="space-y-6">
      <Card className="p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
          className="space-y-3"
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                void submit();
              }
            }}
            rows={3}
            maxLength={2000}
            aria-label="Pergunta"
            placeholder="Pergunte algo sobre seus documentos…"
            className={cn(fieldClasses, "h-auto w-full resize-y py-2.5 leading-relaxed")}
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-sm text-muted">
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
            <div className="flex items-center gap-3">
              <span className="hidden text-xs text-muted sm:inline">Ctrl + Enter</span>
              <Button
                type="submit"
                icon={loading ? Loader2 : SendHorizontal}
                disabled={loading || !question.trim()}
                className={cn(loading && "[&>svg]:animate-spin")}
              >
                {loading ? "Pensando…" : "Perguntar"}
              </Button>
            </div>
          </div>
        </form>
      </Card>

      {!result && !loading && !error && (
        <div className="space-y-2">
          <p className="text-xs font-medium tracking-wider text-muted uppercase">Experimente</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => void submit(s)}
                className="rounded-full border border-border bg-surface px-3 py-1.5 text-left text-sm text-muted transition hover:border-primary/50 hover:text-text"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <Card className="space-y-3 p-5" aria-busy aria-live="polite">
          <p className="flex items-center gap-2 text-sm text-muted">
            <Loader2 className="size-4 animate-spin" aria-hidden />
            Buscando trechos e gerando a resposta…
          </p>
          {[90, 75, 60].map((w) => (
            <div
              key={w}
              className="h-3 animate-pulse rounded bg-surface-2"
              style={{ width: `${w}%` }}
            />
          ))}
        </Card>
      )}

      {error && <Alert>{error}</Alert>}

      {result && !loading && (
        <div ref={answerRef} className="animate-fade-in scroll-mt-6 space-y-5">
          <Card>
            <CardHeader className="justify-between">
              <span className="flex items-center gap-2 font-medium text-text">
                <MessageSquareText className="size-4 text-primary" aria-hidden />
                Resposta
              </span>
              <Verdict r={result} />
            </CardHeader>
            <div className="space-y-4 px-5 py-4">
              <p className="text-sm text-muted">{result.question}</p>
              <AnswerText text={result.answer} validNumbers={valid} onCite={goToSource} />
              {result.warnings.map((w) => (
                <Alert key={w} tone="warning">
                  {w}
                </Alert>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-border px-5 py-2.5 text-xs text-muted">
              <Badge tone="neutral">
                <span className="font-mono">
                  {result.llm_provider}/{result.llm_model}
                </span>
              </Badge>
              <span
                className="inline-flex items-center gap-1"
                title={`busca ${seconds((result.timings.embed_ms ?? 0) + (result.timings.search_ms ?? 0))} · geração ${seconds(result.timings.generate_ms)}`}
              >
                <Clock className="size-3.5" aria-hidden /> {seconds(result.timings.total_ms)}
              </span>
              <span
                className="inline-flex items-center gap-1"
                title={`entrada ${result.usage.prompt_tokens} · saída ${result.usage.completion_tokens} · raciocínio ${result.usage.thinking_tokens}`}
              >
                <Coins className="size-3.5" aria-hidden /> {result.usage.total_tokens} tokens
              </span>
            </div>
          </Card>

          {result.sources.length > 0 && (
            <section className="space-y-3" aria-labelledby="fontes">
              <h2 id="fontes" className="text-base font-semibold text-text">
                Fontes consultadas{" "}
                <span className="font-sans text-sm font-normal text-muted">
                  ({result.cited.length} de {result.sources.length} citadas)
                </span>
              </h2>
              <ol className="space-y-2">
                {result.sources.map((s) => (
                  <li key={s.number}>
                    <SourceCard s={s} highlighted={highlight === s.number} />
                  </li>
                ))}
              </ol>
            </section>
          )}

          <details className="group rounded-xl border border-border bg-surface">
            <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm text-muted hover:text-text [&::-webkit-details-marker]:hidden">
              Ver o prompt enviado à LLM
              <ChevronDown className="size-4 transition group-open:rotate-180" aria-hidden />
            </summary>
            <div className="space-y-3 border-t border-border p-4">
              {result.messages.map((m, i) => (
                <div key={i}>
                  <p className="mb-1 font-mono text-[11px] tracking-wider text-muted uppercase">
                    {m.role}
                  </p>
                  <pre className="max-h-80 overflow-auto rounded-lg bg-surface-2 p-3 font-mono text-xs leading-relaxed whitespace-pre-wrap text-text">
                    {m.content}
                  </pre>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
