import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusBadge } from "@/components/library/StatusBadge";
import {
  ApiError,
  type DocumentChunk,
  type DocumentPage,
  getDocument,
  getDocumentChunks,
  getDocumentPages,
} from "@/lib/api";
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

  const tab = (v: View, label: string) => (
    <Link
      href={v === "paginas" ? `/biblioteca/${id}` : `/biblioteca/${id}?view=chunks`}
      aria-current={view === v ? "page" : undefined}
      className={`border-b-2 px-3 py-2 text-sm ${view === v ? "border-indigo-500 font-medium" : "border-transparent text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200"}`}
    >
      {label}
    </Link>
  );

  return (
    <div className="max-w-4xl space-y-6">
      <Link href="/biblioteca" className="text-sm text-neutral-500 hover:underline">
        ← Biblioteca
      </Link>
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight break-words">{doc.filename}</h1>
        <div className="flex flex-wrap items-center gap-3 text-sm text-neutral-500">
          <StatusBadge status={doc.status} />
          <span className="uppercase">{doc.file_type}</span>
          <span>{formatBytes(doc.size_bytes)}</span>
          <span>{doc.page_count} página(s)</span>
          <span>{doc.chunk_count} chunk(s)</span>
          <span>{doc.char_count.toLocaleString("pt-BR")} caracteres</span>
        </div>
        {doc.error && <p className="text-sm text-red-600">{doc.error}</p>}
      </header>

      <nav className="flex gap-1 border-b border-neutral-200 dark:border-neutral-800">
        {tab("paginas", `Páginas (${pages.length})`)}
        {tab("chunks", `Chunks (${chunks.length})`)}
      </nav>

      {view === "paginas" ? (
        pages.length === 0 ? (
          <p className="text-sm text-neutral-500">Nenhum texto extraído ainda.</p>
        ) : (
          <ol className="space-y-4">
            {pages.map((p) => (
              <li
                key={p.page_number}
                className="rounded-lg border border-neutral-200 dark:border-neutral-800"
              >
                <div className="border-b border-neutral-200 px-4 py-2 text-xs font-medium text-neutral-500 dark:border-neutral-800">
                  Página {p.page_number} · {p.text.length.toLocaleString("pt-BR")} caracteres
                </div>
                <pre className="max-h-96 overflow-auto px-4 py-3 font-sans text-sm whitespace-pre-wrap">
                  {p.text || <span className="text-neutral-400">(página sem texto)</span>}
                </pre>
              </li>
            ))}
          </ol>
        )
      ) : chunks.length === 0 ? (
        <p className="text-sm text-neutral-500">
          Nenhum chunk gerado. Se o documento falhou, confira o erro acima e reprocesse.
        </p>
      ) : (
        <>
          <p className="text-xs text-neutral-500">
            Modelo de embedding: <code className="font-mono">{chunks[0].embedding_model}</code>
          </p>
          <ol className="space-y-3">
            {chunks.map((c) => (
              <li
                key={c.chunk_index}
                className="rounded-lg border border-neutral-200 dark:border-neutral-800"
              >
                <div className="flex flex-wrap gap-x-4 gap-y-1 border-b border-neutral-200 px-4 py-2 text-xs text-neutral-500 dark:border-neutral-800">
                  <span className="font-medium text-neutral-700 dark:text-neutral-300">
                    #{c.chunk_index}
                  </span>
                  <span>{pageLabel(c.page_start, c.page_end)}</span>
                  <span>{c.text.length} caracteres</span>
                  <span>~{c.token_estimate} tokens</span>
                  <span className="font-mono">
                    [{c.char_start}–{c.char_end}]
                  </span>
                </div>
                <p className="px-4 py-3 text-sm whitespace-pre-wrap">{c.text}</p>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
