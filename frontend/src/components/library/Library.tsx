"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
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
import { formatBytes, formatDate } from "@/lib/format";
import { StatusBadge } from "./StatusBadge";

const ALL = "";
const POLL_MS = 2000;

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof TypeError) return "Não foi possível falar com o backend. Ele está rodando?";
  return "Erro inesperado.";
}

export function Library() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
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

  return (
    <div className="grid gap-8 lg:grid-cols-[16rem_1fr]">
      {/* Coleções */}
      <section aria-labelledby="collections-title" className="space-y-3">
        <h2 id="collections-title" className="text-sm font-medium text-neutral-500">
          Coleções
        </h2>
        <ul className="space-y-1 text-sm">
          <li>
            <button
              onClick={() => setSelected(ALL)}
              className={`w-full rounded-md px-3 py-2 text-left ${selected === ALL ? "bg-indigo-50 font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300" : "hover:bg-neutral-100 dark:hover:bg-neutral-900"}`}
            >
              Todos os documentos
            </button>
          </li>
          {collections.map((c) => (
            <li key={c.id} className="group flex items-center">
              <button
                onClick={() => setSelected(c.id)}
                className={`flex-1 truncate rounded-md px-3 py-2 text-left ${selected === c.id ? "bg-indigo-50 font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300" : "hover:bg-neutral-100 dark:hover:bg-neutral-900"}`}
              >
                {c.name} <span className="text-neutral-400">({c.document_count})</span>
              </button>
              <button
                aria-label={`Excluir coleção ${c.name}`}
                title="Excluir coleção (os documentos são mantidos)"
                onClick={() => {
                  if (!confirm(`Excluir a coleção "${c.name}"? Os documentos serão mantidos.`))
                    return;
                  if (selected === c.id) setSelected(ALL);
                  void run(() => deleteCollection(c.id));
                }}
                className="px-2 text-neutral-400 opacity-0 group-hover:opacity-100 hover:text-red-600 focus:opacity-100"
              >
                ×
              </button>
            </li>
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
            maxLength={120}
            className="min-w-0 flex-1 rounded-md border border-neutral-300 bg-transparent px-3 py-1.5 text-sm dark:border-neutral-700"
          />
          <button
            type="submit"
            className="rounded-md bg-neutral-900 px-3 py-1.5 text-sm text-white hover:bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-900"
          >
            Criar
          </button>
        </form>
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
          className={`rounded-lg border-2 border-dashed p-6 text-center text-sm transition ${dragging ? "border-indigo-400 bg-indigo-50 dark:bg-indigo-950/40" : "border-neutral-300 dark:border-neutral-700"}`}
        >
          <p>
            Arraste arquivos aqui ou{" "}
            <button
              onClick={() => fileInput.current?.click()}
              className="font-medium text-indigo-600 underline-offset-2 hover:underline"
            >
              escolha no computador
            </button>
          </p>
          <p className="mt-1 text-neutral-500">
            PDF, DOCX, TXT ou Markdown
            {selectedCollection ? ` · vão para "${selectedCollection.name}"` : " · sem coleção"}
          </p>
          {uploading > 0 && <p className="mt-2 text-amber-600">Enviando {uploading}…</p>}
          <input
            ref={fileInput}
            type="file"
            multiple
            accept={ACCEPTED_EXTENSIONS}
            className="hidden"
            onChange={(e) => void handleFiles(e.target.files)}
          />
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-md bg-red-50 p-3 text-sm whitespace-pre-line text-red-700 dark:bg-red-950 dark:text-red-300"
          >
            {error}
          </p>
        )}

        {documents.length === 0 ? (
          <p className="py-10 text-center text-sm text-neutral-500">Nenhum documento ainda.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-800">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-neutral-500 dark:bg-neutral-900">
                <tr>
                  <th className="px-3 py-2 font-medium">Documento</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 text-right font-medium">Páginas</th>
                  <th className="px-3 py-2 text-right font-medium">Tamanho</th>
                  <th className="px-3 py-2 font-medium">Enviado</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                {documents.map((d) => (
                  <tr key={d.id} className="align-top">
                    <td className="max-w-xs px-3 py-2">
                      <Link
                        href={`/biblioteca/${d.id}`}
                        className="block truncate font-medium hover:underline"
                      >
                        {d.filename}
                      </Link>
                      <span className="text-xs text-neutral-500 uppercase">{d.file_type}</span>
                      {d.error && <p className="mt-1 text-xs text-red-600">{d.error}</p>}
                    </td>
                    <td className="px-3 py-2">
                      <StatusBadge status={d.status} />
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">{d.page_count || "—"}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {formatBytes(d.size_bytes)}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-neutral-500">
                      {formatDate(d.created_at)}
                    </td>
                    <td className="px-3 py-2 text-right whitespace-nowrap">
                      <button
                        onClick={() => void run(() => reprocessDocument(d.id))}
                        disabled={d.status === "processing"}
                        className="text-neutral-500 hover:text-indigo-600 disabled:opacity-40"
                      >
                        Reprocessar
                      </button>
                      <button
                        onClick={() => {
                          if (!confirm(`Excluir "${d.filename}"? O arquivo será apagado.`)) return;
                          void run(() => deleteDocument(d.id));
                        }}
                        className="ml-3 text-neutral-500 hover:text-red-600"
                      >
                        Excluir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
