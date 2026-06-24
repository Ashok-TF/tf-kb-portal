"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  RefreshCw,
  Loader2,
  Trash2,
  // Search,
  FileText,
  Building2,
  RotateCw,
  Download,
  Eye,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RequireAuth } from "@/components/layout/require-auth";
import { UploadZone } from "@/components/kb/upload-zone";
import { CrawlSiteCard } from "@/components/kb/crawl-site-card";
import { ChatPanel } from "@/components/kb/chat-panel";
import { DocumentPreviewModal } from "@/components/kb/document-preview-modal";
import {
  kbApi,
  type DocumentItem,
  type KnowledgeBase,
  viewDocument,
  downloadDocument,
} from "@/lib/api";
import { formatBytes, formatRelativeTime } from "@/lib/utils";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "success" | "warning" | "destructive"> = {
  ready: "success",
  processing: "warning",
  pending: "secondary",
  failed: "destructive",
};

function KbDetail() {
  const { id } = useParams<{ id: string }>();
  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search — commented out for now; uncomment to re-enable semantic search UI.
  // const [query, setQuery] = useState("");
  // const [searching, setSearching] = useState(false);
  // const [matches, setMatches] = useState<SearchMatch[] | null>(null);

  const [fileActionId, setFileActionId] = useState<string | null>(null);
  const [tab, setTab] = useState<"documents" | "chat">("documents");
  const [preview, setPreview] = useState<{
    open: boolean;
    title: string;
    url: string | null;
    message: string | null;
  }>({ open: false, title: "", url: null, message: null });

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadDocs = useCallback(async () => {
    try {
      setDocs(await kbApi.documents(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    }
  }, [id]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [k] = await Promise.all([kbApi.get(id), loadDocs()]);
      setKb(k);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load knowledge base");
    } finally {
      setLoading(false);
    }
  }, [id, loadDocs]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // Poll while any document is still processing.
  useEffect(() => {
    const hasPending = docs.some((d) => d.status === "pending" || d.status === "processing");
    if (hasPending && !pollRef.current) {
      pollRef.current = setInterval(loadDocs, 2000);
    } else if (!hasPending && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [docs, loadDocs]);

  // async function handleSearch(e: React.FormEvent) {
  //   e.preventDefault();
  //   if (!query.trim()) return;
  //   setSearching(true);
  //   try {
  //     const res = await kbApi.search(id, query, 8);
  //     setMatches(res.matches);
  //   } catch (err) {
  //     setError(err instanceof Error ? err.message : "Search failed");
  //   } finally {
  //     setSearching(false);
  //   }
  // }

  async function handleViewDoc(doc: DocumentItem) {
    setFileActionId(doc.id);
    setError(null);
    try {
      const result = await viewDocument(doc);
      if (result.mode === "iframe") {
        setPreview({ open: true, title: doc.filename, url: result.url, message: null });
      } else {
        setPreview({ open: true, title: doc.filename, url: null, message: result.message });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open file");
    } finally {
      setFileActionId(null);
    }
  }

  function closePreview() {
    if (preview.url) URL.revokeObjectURL(preview.url);
    setPreview({ open: false, title: "", url: null, message: null });
  }

  async function handleDownloadDoc(doc: DocumentItem) {
    setFileActionId(doc.id);
    setError(null);
    try {
      await downloadDocument(doc);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setFileActionId(null);
    }
  }

  async function handleDeleteDoc(docId: string) {
    if (!confirm("Delete this document and its vectors?")) return;
    try {
      await kbApi.deleteDocument(docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function handleReindex(docId: string) {
    try {
      await kbApi.reindexDocument(docId);
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reindex failed");
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-64 animate-pulse rounded bg-muted" />
        <div className="h-40 animate-pulse rounded bg-muted" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <Link href="/" className="mt-1 text-muted-foreground hover:text-foreground">
          <ChevronLeft className="h-5 w-5" />
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold">{kb?.name}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            {kb?.department && (
              <span className="inline-flex items-center gap-1">
                <Building2 className="h-3.5 w-3.5" />
                {kb.department}
              </span>
            )}
            <span>{docs.length} documents</span>
          </div>
          {kb?.description && <p className="mt-1 text-sm text-muted-foreground">{kb.description}</p>}
        </div>
        <Button variant="outline" size="sm" onClick={loadAll}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex gap-2 border-b">
        <button
          type="button"
          onClick={() => setTab("documents")}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            tab === "documents"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Documents
        </button>
        <button
          type="button"
          onClick={() => setTab("chat")}
          className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
            tab === "chat"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Chat
        </button>
      </div>

      {error && (
        <div className="flex items-center justify-between rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          <span>{error}</span>
          <Button variant="ghost" size="icon-sm" onClick={() => setError(null)}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {tab === "chat" ? (
        <Card>
          <CardContent className="p-5">
            <h2 className="mb-3 font-semibold">Ask this knowledge base</h2>
            <ChatPanel kbId={id} documents={docs} />
          </CardContent>
        </Card>
      ) : (
        <>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="p-5">
            <h2 className="mb-3 font-semibold">Upload documents</h2>
            <UploadZone kbId={id} onUploaded={loadDocs} />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <h2 className="mb-3 font-semibold">Crawl website</h2>
            <CrawlSiteCard kbId={id} onStarted={loadDocs} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-5">
          <h2 className="mb-3 font-semibold">Documents</h2>
          {docs.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No documents yet. Upload files above to get started.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground">
                    <th className="pb-2 font-medium">Name</th>
                    <th className="pb-2 font-medium">Status</th>
                    <th className="pb-2 font-medium">Chunks</th>
                    <th className="pb-2 font-medium">Size</th>
                    <th className="pb-2 font-medium">Uploaded</th>
                    <th className="pb-2" />
                  </tr>
                </thead>
                <tbody>
                  {docs.map((doc) => (
                    <tr key={doc.id} className="border-b last:border-0">
                      <td className="py-2.5 pr-3">
                        <div className="flex min-w-0 items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleViewDoc(doc)}
                            disabled={fileActionId === doc.id}
                            className="group inline-flex min-w-0 flex-1 items-center gap-1.5 text-left font-medium transition-colors hover:text-primary disabled:opacity-50"
                            title="View file"
                          >
                            <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground group-hover:text-primary" />
                            <span className="truncate underline-offset-2 group-hover:underline">
                              {doc.filename}
                            </span>
                          </button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            title="Download"
                            onClick={() => handleDownloadDoc(doc)}
                            disabled={fileActionId === doc.id}
                          >
                            {fileActionId === doc.id ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                            ) : (
                              <Download className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
                            )}
                          </Button>
                        </div>
                        {doc.status === "failed" && doc.error && (
                          <p className="mt-0.5 text-xs text-destructive">{doc.error}</p>
                        )}
                      </td>
                      <td className="py-2.5 pr-3">
                        <Badge variant={STATUS_VARIANT[doc.status] ?? "secondary"}>
                          {(doc.status === "processing" || doc.status === "pending") && (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          )}
                          {doc.status}
                        </Badge>
                      </td>
                      <td className="py-2.5 pr-3 text-muted-foreground">{doc.chunk_count}</td>
                      <td className="py-2.5 pr-3 text-muted-foreground">{formatBytes(doc.size_bytes)}</td>
                      <td className="py-2.5 pr-3 text-muted-foreground">
                        {formatRelativeTime(doc.created_at)}
                      </td>
                      <td className="py-2.5 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          title="View"
                          className="mr-1 h-8 px-2"
                          onClick={() => handleViewDoc(doc)}
                          disabled={fileActionId === doc.id}
                        >
                          <Eye className="h-3.5 w-3.5" />
                          View
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          title="Reindex"
                          onClick={() => handleReindex(doc.id)}
                        >
                          <RotateCw className="h-3.5 w-3.5 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          title="Delete"
                          onClick={() => handleDeleteDoc(doc.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
        </>
      )}

      <DocumentPreviewModal
        open={preview.open}
        title={preview.title}
        url={preview.url}
        message={preview.message}
        onClose={closePreview}
      />
    </div>
  );
}

export default function Page() {
  return (
    <RequireAuth>
      <KbDetail />
    </RequireAuth>
  );
}
