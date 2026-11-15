import type { DocumentStatus } from "./api";

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export const STATUS_LABEL: Record<DocumentStatus, string> = {
  uploaded: "Na fila",
  processing: "Processando",
  processed: "Processado",
  failed: "Falhou",
};

export const STATUS_STYLE: Record<DocumentStatus, string> = {
  uploaded: "bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300",
  processing: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  processed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
};
