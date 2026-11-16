"use client";

import {
  FileText,
  Folder,
  FolderOpen,
  FolderPlus,
  Inbox,
  Loader2,
  RefreshCw,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Alert, Button, Card, EmptyState, fieldClasses } from "@/components/ui";
import {
  ACCEPTED_EXTENSIONS,
  ApiError,
  type Collection,
  createCollection,
  deleteCollection,
  deleteDocument,
  type DocumentItem,
  listCollections,
  listDocuments,
  reprocessDocument,
  uploadDocument,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatBytes, formatDate } from "@/lib/format";
import { StatusBadge } from "./StatusBadge";

const ALL = "";
const POLL_MS = 2000;

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof TypeError) return "Não foi possível falar com o backend. Ele está rodando?";
  return "Erro inesperado.";
}

function CollectionItem({
  label,
  count,
  active,
  onSelect,
  onDelete,
}: {
  label: string;
  count?: number;
  active: boolean;
  onSelect: () => void;
  onDelete?: () => void;
}) {
  const Icon = active ? FolderOpen : Folder;
  return (
    <li className="group flex items-center">
      <button
        type="button"
        onClick={onSelect}
        aria-pressed={active}
        className={cn(
          "flex min-w-0 flex-1 items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-colors",
          active
            ? "bg-primary-soft font-medium text-text"
            : "text-muted hover:bg-surface-2 hover:text-text",
        )}
      >
        <Icon className={cn("size-4 shrink-0", active && "text-primary")} aria-hidden />
        <span className="flex-1 truncate">{label}</span>
        {count !== undefined && <span className="text-xs text-muted tabular-nums">{count}</span>}
      </button>
      {onDelete && (
        <button
          type="button"
          aria-label={`Excluir coleção ${label}`}
          title="Excluir coleção (os documentos são mantidos)"
          onClick={onDelete}
          className="ml-1 rounded-md p-1.5 text-muted opacity-0 transition group-hover:opacity-100 hover:bg-danger/10 hover:text-danger focus:opacity-100"
        >
          <X className="size-3.5" aria-hidden />
        </button>
      )}
    </li>
  );
}

export function Library() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [selected, setSelected] = useState<string>(ALL);
  const [newName, setNewName] = useState("");
  const [uploading, setUploading] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      const [cols, docs] = await Promise.all([
        listCollections(),
        listDocuments(selected || undefined),
      ]);
      setCollections(cols);
      setDocuments(docs);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoaded(true);
    }
  }, [selected]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Enquanto houver documento na fila ou processando, atualiza periodicamente.
  const pending = documents.some((d) => d.status === "uploaded" || d.status === "processing");
  useEffect(() => {
    if (!pending) return;
    const id = setInterval(() => void refresh(), POLL_MS);
    return () => clearInterval(id);
  }, [pending, refresh]);

  async function run(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(errorMessage(err));
    }
    await refresh();
  }

  async function handleFiles(files: FileList | null) {
    if (!files?.length) return;
    const list = Array.from(files);
    setUploading((n) => n + list.length);
    setError(null);
    const failures: string[] = [];
    await Promise.all(
      list.map(async (file) => {
        try {
          await uploadDocument(file, selected || undefined);
        } catch (err) {
          failures.push(`${file.name}: ${errorMessage(err)}`);
        } finally {
          setUploading((n) => n - 1);
        }
      }),
    );
    if (failures.length) setError(failures.join("\n"));
    if (fileInput.current) fileInput.current.value = "";
    await refresh();
  }

  const selectedCollection = collections.find((c) => c.id === selected);
  const total = collections.reduce((n, c) => n + c.document_count, 0);

  return (
    <div className="grid gap-6 xl:grid-cols-[15rem_1fr]">
      {/* Coleções */}
      <section aria-labelledby="collections-title" className="space-y-3">
        <h2
          id="collections-title"
          className="px-1 font-sans text-[11px] font-medium tracking-wider text-muted uppercase"
        >
          Coleções
        </h2>
        <ul className="space-y-0.5">
          <CollectionItem
            label="Todos os documentos"
            active={selected === ALL}
            onSelect={() => setSelected(ALL)}
          />
          {collections.map((c) => (
            <CollectionItem
              key={c.id}
              label={c.name}
              count={c.document_count}
              active={selected === c.id}
              onSelect={() => setSelected(c.id)}
              onDelete={() => {
                if (!confirm(`Excluir a coleção "${c.name}"? Os documentos serão mantidos.`))
                  return;
                if (selected === c.id) setSelected(ALL);
                void run(() => deleteCollection(c.id));
              }}
            />
          ))}
        </ul>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const name = newName.trim();
            if (!name) return;
            void run(async () => {
              const created = await createCollection(name);
              setNewName("");
              setSelected(created.id);
            });
          }}
          className="flex gap-2"
        >
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Nova coleção"
            aria-label="Nome da nova coleção"
            maxLength={120}
            className={cn(fieldClasses, "h-9 min-w-0 flex-1")}
          />
          <Button
            type="submit"
            variant="secondary"
            size="sm"
            icon={FolderPlus}
            className="h-9"
            aria-label="Criar coleção"
            disabled={!newName.trim()}
          />
        </form>
        {total > 0 && <p className="px-1 text-xs text-muted">{total} documento(s) em coleções</p>}
      </section>

      {/* Upload + lista */}
      <section className="min-w-0 space-y-4">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            void handleFiles(e.dataTransfer.files);
          }}
          className={cn(
            "flex flex-col items-center gap-2 rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors",
            dragging ? "border-primary bg-primary-soft" : "border-border bg-surface",
          )}
        >
          <span
            className={cn(
              "flex size-11 items-center justify-center rounded-full transition-colors",
              dragging ? "bg-primary text-white" : "bg-accent-soft text-accent-text",
            )}
          >
            {uploading > 0 ? (
              <Loader2 className="size-5 animate-spin" aria-hidden />
            ) : (
              <UploadCloud className="size-5" aria-hidden />
            )}
          </span>
          <p className="text-sm text-text">
            Arraste arquivos aqui ou{" "}
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              className="font-medium text-link underline-offset-2 hover:underline"
            >
              escolha no computador
            </button>
          </p>
          <p className="text-xs text-muted">
            PDF, DOCX, TXT ou Markdown
            {selectedCollection ? ` · vão para "${selectedCollection.name}"` : " · sem coleção"}
          </p>
          {uploading > 0 && (
            <p className="text-xs font-medium text-warning" aria-live="polite">
              Enviando {uploading} arquivo(s)…
            </p>
          )}
          <input
            ref={fileInput}
            type="file"
            multiple
            accept={ACCEPTED_EXTENSIONS}
            className="hidden"
            onChange={(e) => void handleFiles(e.target.files)}
          />
        </div>

        {error && <Alert>{error}</Alert>}

        {!loaded ? (
          <Card className="space-y-3 p-4" aria-busy>
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-surface-2" />
            ))}
          </Card>
        ) : documents.length === 0 ? (
          <EmptyState icon={Inbox} title="Nenhum documento ainda">
            Envie um arquivo acima para começar a montar sua base de conhecimento.
          </EmptyState>
        ) : (
          <Card className="relative overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-surface-2 text-left text-xs text-muted">
                <tr>
                  <th className="w-full px-4 py-2.5 font-medium">Documento</th>
                  <th className="px-3 py-2.5 font-medium">Status</th>
                  <th className="hidden px-3 py-2.5 text-right font-medium sm:table-cell">
                    Páginas
                  </th>
                  <th className="hidden px-3 py-2.5 text-right font-medium sm:table-cell">
                    Chunks
                  </th>
                  <th className="hidden px-3 py-2.5 text-right font-medium md:table-cell">
                    Tamanho
                  </th>
                  <th className="hidden px-3 py-2.5 font-medium xl:table-cell">Enviado</th>
                  <th className="px-3 py-2.5">
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {documents.map((d) => (
                  <tr key={d.id} className="align-top transition-colors hover:bg-surface-2/60">
                    <td className="w-full max-w-0 px-4 py-3">
                      <div className="flex items-start gap-2.5">
                        <FileText className="mt-0.5 size-4 shrink-0 text-muted" aria-hidden />
                        <div className="min-w-0">
                          <Link
                            href={`/biblioteca/${d.id}`}
                            className="block truncate font-medium text-text hover:text-link"
                          >
                            {d.filename}
                          </Link>
                          <span className="text-xs text-muted uppercase">{d.file_type}</span>
                          {d.error && <p className="mt-1 text-xs text-danger">{d.error}</p>}
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge status={d.status} />
                    </td>
                    <td className="hidden px-3 py-3 text-right text-muted tabular-nums sm:table-cell">
                      {d.page_count || "—"}
                    </td>
                    <td className="hidden px-3 py-3 text-right text-muted tabular-nums sm:table-cell">
                      {d.chunk_count || "—"}
                    </td>
                    <td className="hidden px-3 py-3 text-right text-muted tabular-nums md:table-cell">
                      {formatBytes(d.size_bytes)}
                    </td>
                    <td className="hidden px-3 py-3 whitespace-nowrap text-muted xl:table-cell">
                      {formatDate(d.created_at)}
                    </td>
                    <td className="px-2 py-2">
                      <div className="flex justify-end gap-0.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={RefreshCw}
                          aria-label={`Reprocessar ${d.filename}`}
                          title="Reprocessar"
                          disabled={d.status === "processing"}
                          onClick={() => void run(() => reprocessDocument(d.id))}
                        />
                        <Button
                          variant="danger"
                          size="sm"
                          icon={Trash2}
                          aria-label={`Excluir ${d.filename}`}
                          title="Excluir"
                          onClick={() => {
                            if (!confirm(`Excluir "${d.filename}"? O arquivo será apagado.`))
                              return;
                            void run(() => deleteDocument(d.id));
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </section>
    </div>
  );
}
