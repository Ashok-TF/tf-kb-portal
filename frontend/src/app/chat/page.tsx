"use client";

import { useState } from "react";
import { Loader2, Send, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RequireAuth } from "@/components/layout/require-auth";
import { kbApi, type ChatCitation } from "@/lib/api";

function GlobalChat() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<ChatCitation[]>([]);
  const [selectedKbs, setSelectedKbs] = useState<{ id: string; name: string; score: number }[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await kbApi.globalChat(query.trim());
      setAnswer(res.answer);
      setCitations(res.citations);
      setSelectedKbs(res.selected_kbs ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ask across knowledge bases</h1>
        <p className="text-sm text-muted-foreground">
          The agent picks the most relevant knowledge base(s) for your question.
        </p>
      </div>

      <Card>
        <CardContent className="p-5 space-y-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Where is the latest AI sales deck?"
            />
            <Button type="submit" disabled={loading || !query.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>

          {selectedKbs.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedKbs.map((kb) => (
                <Badge key={kb.id} variant="outline">
                  {kb.name} ({kb.score.toFixed(2)})
                </Badge>
              ))}
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          {answer && (
            <div className="rounded-md border bg-muted/30 p-4">
              <p className="text-sm whitespace-pre-wrap">{answer}</p>
            </div>
          )}

          {citations.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase text-muted-foreground">Citations</h3>
              {citations.map((c, i) => (
                <div key={`${c.document_id}-${i}`} className="rounded-md border p-3 text-sm">
                  <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
                    <FileText className="h-3 w-3" />
                    {c.kb_name && <Badge variant="secondary">{c.kb_name}</Badge>}
                    <span className="truncate">{c.filename}</span>
                    <span className="ml-auto">score {c.score.toFixed(3)}</span>
                  </div>
                  <p className="line-clamp-3 text-xs">{c.excerpt}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ChatPage() {
  return (
    <RequireAuth>
      <GlobalChat />
    </RequireAuth>
  );
}
