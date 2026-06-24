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
  summary?: string | null;
  entities_json?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatCitation {
  document_id: string;
  filename: string;
  kb_id: string;
  kb_name?: string | null;
  chunk_index: number;
  score: number;
  excerpt: string;
}

export interface ChatResponse {
  answer: string;
  citations: ChatCitation[];
  selected_kbs?: { id: string; name: string; score: number }[];
}

export interface AuditLogItem {
  id: string;
  user_email: string;
  action: string;
  kb_id: string | null;
  document_id: string | null;
  detail: string | null;
  created_at: string;
}

export type PreviewResult =
  | { mode: "iframe"; url: string }
  | { mode: "unsupported"; message: string };

const OFFICE_EXTENSIONS = new Set(["doc", "docx", "ppt", "pptx", "xls", "xlsx", "xlsm"]);
const PREVIEWABLE_EXTENSIONS = new Set(["pdf", "png", "jpg", "jpeg", "gif", "webp", "txt", "md", "csv"]);

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
  update: (id: string, body: { name?: string; description?: string; department?: string }) =>
    api<KnowledgeBase>(`/api/knowledge-bases/${id}`, { method: "PATCH", body }),
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
  chat: (id: string, query: string, topK = 5) =>
    api<ChatResponse>(`/api/knowledge-bases/${id}/chat`, {
      method: "POST",
      body: { query, top_k: topK },
    }),
  crawl: (id: string, url: string, maxDepth: number) =>
    api<{ status: string; message: string }>(`/api/knowledge-bases/${id}/crawl`, {
      method: "POST",
      body: { url, max_depth: maxDepth },
    }),
  globalChat: (query: string, topK = 5) =>
    api<ChatResponse>("/api/chat", { method: "POST", body: { query, top_k: topK } }),
  auditLogs: (limit = 100) => api<AuditLogItem[]>(`/api/admin/audit?limit=${limit}`),
};

async function fetchDocumentFile(docId: string, download = false): Promise<Blob> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const qs = download ? "?download=true" : "";
  const res = await fetch(`${API_BASE_URL}/api/documents/${docId}/file${qs}`, { headers });

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

  return res.blob();
}

export async function getDocumentPreview(doc: DocumentItem): Promise<PreviewResult> {
  const ext = (doc.file_extension || doc.filename.split(".").pop() || "").toLowerCase();
  if (OFFICE_EXTENSIONS.has(ext)) {
    return {
      mode: "unsupported",
      message: "Preview is not supported for Office files in the browser. Please use Download.",
    };
  }
  if (!PREVIEWABLE_EXTENSIONS.has(ext)) {
    return {
      mode: "unsupported",
      message: `Preview is not available for .${ext} files. Please use Download.`,
    };
  }
  const blob = await fetchDocumentFile(doc.id);
  const url = URL.createObjectURL(blob);
  return { mode: "iframe", url };
}

export async function viewDocument(doc: DocumentItem): Promise<PreviewResult> {
  return getDocumentPreview(doc);
}

export async function downloadDocument(doc: DocumentItem): Promise<void> {
  const blob = await fetchDocumentFile(doc.id, true);
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = doc.filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
