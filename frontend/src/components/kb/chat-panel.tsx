"use client";

import { useState } from "react";
import { Loader2, Send, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { kbApi, type ChatCitation, viewDocument, type DocumentItem } from "@/lib/api";

interface ChatPanelProps {
  kbId: string;
  documents: DocumentItem[];
}

export function ChatPanel({ kbId, documents }: ChatPanelProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<ChatCitation[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await kbApi.chat(kbId, query.trim());
      setAnswer(res.answer);
      setCitations(res.citations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setLoading(false);
    }
  }

  async function openCitation(c: ChatCitation) {
    const doc = documents.find((d) => d.id === c.document_id);
    if (!doc) return;
    const result = await viewDocument(doc);
    if (result.mode === "unsupported") {
      setError(result.message);
    }
    // Preview handled by parent if needed; citations could open in new tab for iframe mode
    if (result.mode === "iframe") {
      window.open(result.url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(result.url), 60_000);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about this knowledge base..."
        />
        <Button type="submit" disabled={loading || !query.trim()}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </Button>
      </form>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {answer && (
        <div className="rounded-md border bg-muted/30 p-4">
          <p className="text-sm whitespace-pre-wrap">{answer}</p>
        </div>
      )}

      {citations.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Sources
          </h3>
          {citations.map((c, i) => (
            <button
              key={`${c.document_id}-${c.chunk_index}-${i}`}
              type="button"
              onClick={() => openCitation(c)}
              className="w-full rounded-md border p-3 text-left text-sm transition-colors hover:bg-muted/50"
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1 font-medium">
                  <FileText className="h-3 w-3" />
                  {c.filename}
                </span>
                <span className="text-xs text-muted-foreground">score {c.score.toFixed(3)}</span>
              </div>
              <p className="line-clamp-3 text-xs text-muted-foreground">{c.excerpt}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
