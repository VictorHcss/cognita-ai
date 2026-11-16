export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
  app: string;
  version: string;
  env: string;
  llm_provider: string;
  embedding_provider: string;
};

export type Collection = {
  id: string;
  name: string;
  description: string;
  created_at: string;
  document_count: number;
};

export type DocumentStatus = "uploaded" | "processing" | "processed" | "failed";

export type DocumentItem = {
  id: string;
  collection_id: string | null;
  filename: string;
  file_type: "pdf" | "docx" | "txt" | "md";
  size_bytes: number;
  status: DocumentStatus;
  error: string | null;
  page_count: number;
  char_count: number;
  chunk_count: number;
  created_at: string;
  updated_at: string;
};

export type DocumentPage = { page_number: number; text: string };

export type DocumentChunk = {
  chunk_index: number;
  text: string;
  page_start: number;
  page_end: number;
  char_start: number;
  char_end: number;
  token_estimate: number;
  embedding_model: string;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = typeof body?.detail === "string" ? body.detail : res.statusText;
    throw new ApiError(res.status, detail);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const getHealth = () => request<HealthResponse>("/api/health");

export const listCollections = () => request<Collection[]>("/api/collections");
export const createCollection = (name: string, description = "") =>
  request<Collection>("/api/collections", json("POST", { name, description }));
export const deleteCollection = (id: string) =>
  request<void>(`/api/collections/${id}`, { method: "DELETE" });

export const listDocuments = (collectionId?: string) =>
  request<DocumentItem[]>(
    `/api/documents${collectionId ? `?collection_id=${encodeURIComponent(collectionId)}` : ""}`,
  );
export const getDocument = (id: string) => request<DocumentItem>(`/api/documents/${id}`);
export const getDocumentPages = (id: string) =>
  request<DocumentPage[]>(`/api/documents/${id}/pages`);
export const getDocumentChunks = (id: string) =>
  request<DocumentChunk[]>(`/api/documents/${id}/chunks`);
export const reprocessDocument = (id: string) =>
  request<DocumentItem>(`/api/documents/${id}/reprocess`, { method: "POST" });
export const deleteDocument = (id: string) =>
  request<void>(`/api/documents/${id}`, { method: "DELETE" });

export function uploadDocument(file: File, collectionId?: string) {
  const form = new FormData();
  form.append("file", file);
  if (collectionId) form.append("collection_id", collectionId);
  return request<DocumentItem>("/api/documents", { method: "POST", body: form });
}

export const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.md,.markdown";

export type SearchResult = {
  rank: number;
  score: number;
  chunk_id: number;
  chunk_index: number;
  document_id: string;
  filename: string;
  collection_id: string | null;
  page_start: number;
  page_end: number;
  text: string;
};

export type SearchResponse = {
  query: string;
  embedding_model: string;
  results: SearchResult[];
  embed_ms: number;
  search_ms: number;
  warnings: string[];
};

export type SearchParams = {
  query: string;
  top_k?: number;
  collection_id?: string;
  document_id?: string;
  min_score?: number;
};

export const searchChunks = (params: SearchParams) =>
  request<SearchResponse>("/api/search", json("POST", params));

export type AnswerSource = {
  number: number;
  chunk_id: number;
  chunk_index: number;
  document_id: string;
  filename: string;
  page_start: number;
  page_end: number;
  score: number;
  text: string;
  cited: boolean;
};

export type AskResponse = {
  question: string;
  answer: string;
  grounded: boolean;
  not_found: boolean;
  cited: number[];
  invalid_citations: number[];
  sources: AnswerSource[];
  llm_provider: string;
  llm_model: string;
  embedding_model: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    thinking_tokens: number;
    total_tokens: number;
  };
  finish_reason: string | null;
  timings: Record<string, number>;
  messages: { role: string; content: string }[];
  warnings: string[];
};

export type AskParams = {
  question: string;
  top_k?: number;
  collection_id?: string;
  document_id?: string;
  min_score?: number;
};

export const askQuestion = (params: AskParams) =>
  request<AskResponse>("/api/ask", json("POST", params));
