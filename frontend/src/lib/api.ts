const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

const TOKEN_KEY = "kb_portal_token";
const EMAIL_KEY = "kb_portal_email";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getEmail(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(EMAIL_KEY);
}

export function setSession(token: string, email: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(EMAIL_KEY, email);
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(EMAIL_KEY);
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) return body.detail.map((d: { msg?: string }) => d.msg).join(", ");
    return `Request failed (HTTP ${res.status})`;
  } catch {
    return `Request failed (HTTP ${res.status})`;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  isForm?: boolean;
}

export async function api<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let body: BodyInit | undefined;
  if (opts.isForm) {
    body = opts.body as FormData;
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: opts.method ?? "GET",
    headers,
    body,
  });

  if (res.status === 401) {
    clearSession();
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Session expired. Please sign in again.");
  }

  if (!res.ok) {
    throw new ApiError(res.status, await parseError(res));
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// --- Typed helpers ---
export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  department: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  document_count: number;
  ready_count: number;
}

export interface DocumentItem {
  id: string;
  kb_id: string;
  filename: string;
  content_type: string | null;
  file_extension: string | null;
  size_bytes: number;
  status: "pending" | "processing" | "ready" | "failed";
  chunk_count: number;
  char_count: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface SearchMatch {
  document_id: string;
  filename: string;
  chunk_index: number;
  score: number;
  text: string;
}

export const kbApi = {
  list: () => api<KnowledgeBase[]>("/api/knowledge-bases"),
  get: (id: string) => api<KnowledgeBase>(`/api/knowledge-bases/${id}`),
  create: (body: { name: string; description?: string; department?: string }) =>
    api<KnowledgeBase>("/api/knowledge-bases", { method: "POST", body }),
  remove: (id: string) => api<void>(`/api/knowledge-bases/${id}`, { method: "DELETE" }),
  documents: (id: string) => api<DocumentItem[]>(`/api/knowledge-bases/${id}/documents`),
  upload: (id: string, formData: FormData) =>
    api<DocumentItem>(`/api/knowledge-bases/${id}/documents`, {
      method: "POST",
      body: formData,
      isForm: true,
    }),
  search: (id: string, query: string, topK = 5) =>
    api<{ query: string; matches: SearchMatch[] }>(`/api/knowledge-bases/${id}/search`, {
      method: "POST",
      body: { query, top_k: topK },
    }),
  deleteDocument: (docId: string) => api<void>(`/api/documents/${docId}`, { method: "DELETE" }),
  reindexDocument: (docId: string) =>
    api<DocumentItem>(`/api/documents/${docId}/reindex`, { method: "POST" }),
};
