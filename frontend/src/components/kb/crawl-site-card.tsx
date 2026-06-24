"use client";

import { useState } from "react";
import { Globe, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { kbApi } from "@/lib/api";

interface CrawlSiteCardProps {
  kbId: string;
  onStarted?: () => void;
}

export function CrawlSiteCard({ kbId, onStarted }: CrawlSiteCardProps) {
  const [url, setUrl] = useState("");
  const [depth, setDepth] = useState("1");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleCrawl(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await kbApi.crawl(kbId, url.trim(), Number(depth));
      setMessage(res.message);
      onStarted?.();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Crawl failed");
    } finally {
      setLoading(false);
    }
  }

  function handleComingSoon() {
    setMessage("Website crawling coming in v2 — use file upload for now.");
  }

  return (
    <form onSubmit={handleCrawl} className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row">
        <Input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/docs"
          type="url"
        />
        <select
          value={depth}
          onChange={(e) => setDepth(e.target.value)}
          className="h-9 rounded-md border bg-background px-3 text-sm"
          aria-label="Crawl depth"
        >
          <option value="1">1 level</option>
          <option value="2">2 levels</option>
          <option value="3">3 levels</option>
        </select>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button type="submit" size="sm" disabled={loading || !url.trim()}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Globe className="h-4 w-4 mr-1.5" />}
          Start crawl
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={handleComingSoon}>
          Preview (stub)
        </Button>
      </div>
      {message && <p className="text-sm text-muted-foreground">{message}</p>}
    </form>
  );
}
