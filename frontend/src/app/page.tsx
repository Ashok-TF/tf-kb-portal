"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Plus,
  BookOpen,
  FileText,
  Trash2,
  Loader2,
  RefreshCw,
  Building2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { RequireAuth } from "@/components/layout/require-auth";
import { kbApi, type KnowledgeBase } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

function Dashboard() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const [name, setName] = useState("");
  const [department, setDepartment] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setKbs(await kbApi.list());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load knowledge bases");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await kbApi.create({ name, description, department });
      setName("");
      setDepartment("");
      setDescription("");
      setShowCreate(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create knowledge base");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this knowledge base and all its documents? This cannot be undone.")) return;
    setDeletingId(id);
    try {
      await kbApi.remove(id);
      setKbs((prev) => prev.filter((k) => k.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Knowledge Bases</h1>
          <p className="text-sm text-muted-foreground">
            Create a knowledge base per department, then upload documents to make them searchable.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={load} disabled={loading}>
            <RefreshCw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
          </Button>
          <Button size="sm" onClick={() => setShowCreate((s) => !s)}>
            <Plus className="h-4 w-4 mr-1.5" />
            New Knowledge Base
          </Button>
        </div>
      </div>

      {showCreate && (
        <Card>
          <CardContent className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold">Create knowledge base</h2>
              <Button variant="ghost" size="icon-sm" onClick={() => setShowCreate(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <form onSubmit={handleCreate} className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Name</label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. HR Policies"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Department</label>
                  <Input
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="e.g. Human Resources"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Description</label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What kind of documents will live here?"
                />
              </div>
              <div className="flex justify-end">
                <Button type="submit" disabled={creating || !name.trim()}>
                  {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-5">
                <div className="h-20 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : kbs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <BookOpen className="mb-4 h-12 w-12 text-muted-foreground/40" />
          <h2 className="text-lg font-semibold">No knowledge bases yet</h2>
          <p className="mt-1 max-w-md text-sm text-muted-foreground">
            Create your first knowledge base to start uploading and processing documents.
          </p>
          <Button className="mt-4" onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1.5" />
            Create Knowledge Base
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {kbs.map((kb) => (
            <Card key={kb.id} className="group transition-colors hover:border-primary/40">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <Link href={`/kb/${kb.id}`} className="min-w-0 flex-1">
                    <h3 className="font-semibold group-hover:text-primary">{kb.name}</h3>
                    {kb.department && (
                      <span className="mt-1 inline-flex items-center gap-1 text-xs text-muted-foreground">
                        <Building2 className="h-3 w-3" />
                        {kb.department}
                      </span>
                    )}
                  </Link>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => handleDelete(kb.id)}
                    disabled={deletingId === kb.id}
                  >
                    {deletingId === kb.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
                    )}
                  </Button>
                </div>

                {kb.description && (
                  <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{kb.description}</p>
                )}

                <Link href={`/kb/${kb.id}`}>
                  <div className="mt-4 flex items-center gap-4 border-t pt-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      {kb.document_count} docs
                    </span>
                    <Badge variant={kb.ready_count === kb.document_count ? "success" : "secondary"}>
                      {kb.ready_count} ready
                    </Badge>
                    <span className="ml-auto">Updated {formatRelativeTime(kb.updated_at)}</span>
                  </div>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Page() {
  return (
    <RequireAuth>
      <Dashboard />
    </RequireAuth>
  );
}
