import Link from "next/link";
import { notFound } from "next/navigation";
import { StatusBadge } from "@/components/library/StatusBadge";
import { ApiError, getDocument, getDocumentPages } from "@/lib/api";
import { formatBytes } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let doc, pages;
  try {
    [doc, pages] = await Promise.all([getDocument(id), getDocumentPages(id)]);
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 422)) notFound();
    throw err;
  }

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
          <span>{doc.char_count.toLocaleString("pt-BR")} caracteres</span>
        </div>
        {doc.error && <p className="text-sm text-red-600">{doc.error}</p>}
      </header>

      {pages.length === 0 ? (
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
      )}
    </div>
  );
}
