"use client";

import { useCallback, useRef, useState } from "react";
import {
  Upload,
  FileText,
  X,
  CheckCircle2,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { kbApi } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";

interface UploadZoneProps {
  kbId: string;
  onUploaded: () => void;
}

interface Entry {
  file: File;
  id: string;
  status: "queued" | "uploading" | "done" | "error";
  error?: string;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024;

const ACCEPTED = [
  ".pdf", ".txt", ".md", ".csv", ".json",
  ".docx", ".pptx", ".xlsx",
  ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp",
];

export function UploadZone({ kbId, onUploaded }: UploadZoneProps) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((files: FileList | File[]) => {
    const next: Entry[] = [];
    for (const f of Array.from(files)) {
      const ext = "." + (f.name.split(".").pop()?.toLowerCase() ?? "");
      if (!ACCEPTED.includes(ext)) continue;
      if (f.size > MAX_FILE_SIZE) {
        next.push({ file: f, id: crypto.randomUUID(), status: "error", error: "Exceeds 50 MB" });
        continue;
      }
      next.push({ file: f, id: crypto.randomUUID(), status: "queued" });
    }
    setEntries((prev) => [...prev, ...next]);
  }, []);

  async function uploadAll() {
    setUploading(true);
    try {
      for (const entry of entries) {
        if (entry.status !== "queued") continue;
        setEntries((prev) =>
          prev.map((e) => (e.id === entry.id ? { ...e, status: "uploading" } : e))
        );
        try {
          const formData = new FormData();
          formData.append("file", entry.file);
          await kbApi.upload(kbId, formData);
          setEntries((prev) =>
            prev.map((e) => (e.id === entry.id ? { ...e, status: "done" } : e))
          );
        } catch (err) {
          setEntries((prev) =>
            prev.map((e) =>
              e.id === entry.id
                ? { ...e, status: "error", error: err instanceof Error ? err.message : "Failed" }
                : e
            )
          );
        }
      }
      onUploaded();
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        className={cn(
          "cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors",
          dragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
        )}
      >
        <Upload className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium">
          Drop files here or <span className="text-primary">browse</span>
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          PDF, TXT, MD, CSV, DOCX, PPTX, XLSX, images — up to 50 MB each
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {entries.length > 0 && (
        <div className="space-y-2">
          {entries.map((entry) => (
            <div key={entry.id} className="flex items-center gap-3 rounded-md bg-muted/50 p-2 text-sm">
              <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium">{entry.file.name}</p>
                <span className="text-[11px] text-muted-foreground">
                  {formatBytes(entry.file.size)}
                  {entry.error ? ` — ${entry.error}` : ""}
                </span>
              </div>
              {entry.status === "queued" && (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => setEntries((prev) => prev.filter((e) => e.id !== entry.id))}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
              {entry.status === "uploading" && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
              {entry.status === "done" && <CheckCircle2 className="h-4 w-4 text-green-600" />}
              {entry.status === "error" && <AlertCircle className="h-4 w-4 text-destructive" />}
            </div>
          ))}
          <div className="flex items-center justify-between pt-1">
            <span className="text-xs text-muted-foreground">{entries.length} file(s) selected</span>
            <Button
              size="sm"
              onClick={uploadAll}
              disabled={uploading || entries.every((e) => e.status !== "queued")}
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-1.5" />
                  Upload &amp; Process
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
