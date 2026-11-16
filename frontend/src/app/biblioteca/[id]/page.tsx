import { ArrowLeft, Boxes, FileText, ScrollText } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusBadge } from "@/components/library/StatusBadge";
import { Alert, Badge, Card, CardHeader, EmptyState } from "@/components/ui";
import {
  ApiError,
  type DocumentChunk,
  type DocumentPage,
  getDocument,
  getDocumentChunks,
  getDocumentPages,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatBytes } from "@/lib/format";

export const dynamic = "force-dynamic";

type View = "paginas" | "chunks";

function pageLabel(start: number, end: number) {
  return start === end ? `p. ${start}` : `p. ${start}–${end}`;
}

export default async function DocumentDetail({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ view?: string }>;
}) {
  const { id } = await params;
  const view: View = (await searchParams).view === "chunks" ? "chunks" : "paginas";

  let doc, pages: DocumentPage[], chunks: DocumentChunk[];
  try {
    [doc, pages, chunks] = await Promise.all([
      getDocument(id),
      getDocumentPages(id),
      getDocumentChunks(id),
    ]);
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 422)) notFound();
    throw err;
  }

  const tabs = [
    { key: "paginas" as const, label: "Páginas", count: pages.length, icon: ScrollText },
    { key: "chunks" as const, label: "Chunks", count: chunks.length, icon: Boxes },
  ];

  return (
    <div className="animate-fade-in space-y-6">
      <Link
        href="/biblioteca"
        className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-text"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Biblioteca
      </Link>

      <header className="flex items-start gap-3">
        <span className="mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-lg border border-border bg-surface text-primary">
          <FileText className="size-5" aria-hidden />
        </span>
        <div className="min-w-0 space-y-2">
          <h1 className="text-2xl font-semibold break-words text-text">{doc.filename}</h1>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
            <StatusBadge status={doc.status} />
            <Badge>{doc.file_type.toUpperCase()}</Badge>
            <span>{formatBytes(doc.size_bytes)}</span>
            <span aria-hidden>·</span>
            <span>{doc.page_count} página(s)</span>
            <span aria-hidden>·</span>
            <span>{doc.chunk_count} chunk(s)</span>
            <span aria-hidden>·</span>
            <span>{doc.char_count.toLocaleString("pt-BR")} caracteres</span>
          </div>
        </div>
      </header>

      {doc.error && <Alert>{doc.error}</Alert>}

      <nav className="flex gap-1 border-b border-border" aria-label="Visualização">
        {tabs.map(({ key, label, count, icon: Icon }) => {
          const active = view === key;
          return (
            <Link
              key={key}
              href={key === "paginas" ? `/biblioteca/${id}` : `/biblioteca/${id}?view=chunks`}
              aria-current={active ? "page" : undefined}
              className={cn(
                "-mb-px flex items-center gap-2 border-b-2 px-3 py-2.5 text-sm transition-colors",
                active
                  ? "border-primary font-medium text-text"
                  : "border-transparent text-muted hover:text-text",
              )}
            >
              <Icon className="size-4" aria-hidden />
              {label}
              <span className="rounded-full bg-surface-2 px-1.5 text-xs text-muted tabular-nums">
                {count}
              </span>
            </Link>
          );
        })}
      </nav>

      {view === "paginas" ? (
        pages.length === 0 ? (
          <EmptyState icon={ScrollText} title="Nenhum texto extraído ainda" />
        ) : (
          <ol className="space-y-4">
            {pages.map((p) => (
              <li key={p.page_number}>
                <Card>
                  <CardHeader>
                    <span className="font-medium text-text">Página {p.page_number}</span>
                    <span>{p.text.length.toLocaleString("pt-BR")} caracteres</span>
                  </CardHeader>
                  <pre className="max-h-96 overflow-auto px-4 py-3 font-sans text-sm leading-relaxed whitespace-pre-wrap text-text">
                    {p.text || <span className="text-muted">(página sem texto)</span>}
                  </pre>
                </Card>
              </li>
            ))}
          </ol>
        )
      ) : chunks.length === 0 ? (
        <EmptyState icon={Boxes} title="Nenhum chunk gerado">
          Se o documento falhou, confira o erro acima e reprocesse.
        </EmptyState>
      ) : (
        <div className="space-y-3">
          <p className="flex flex-wrap items-center gap-2 text-xs text-muted">
            Modelo de embedding
            <Badge tone="accent">
              <span className="font-mono">{chunks[0].embedding_model}</span>
            </Badge>
          </p>
          <ol className="space-y-3">
            {chunks.map((c) => (
              <li key={c.chunk_index}>
                <Card>
                  <CardHeader>
                    <span className="font-mono font-medium text-text">#{c.chunk_index}</span>
                    <Badge tone="info">{pageLabel(c.page_start, c.page_end)}</Badge>
                    <span>{c.text.length} caracteres</span>
                    <span>~{c.token_estimate} tokens</span>
                    <span className="font-mono">
                      [{c.char_start}–{c.char_end}]
                    </span>
                  </CardHeader>
                  <p className="px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap text-text">
                    {c.text}
                  </p>
                </Card>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
