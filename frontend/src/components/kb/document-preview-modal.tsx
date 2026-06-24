"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DocumentPreviewModalProps {
  open: boolean;
  title: string;
  url: string | null;
  message: string | null;
  onClose: () => void;
}

export function DocumentPreviewModal({
  open,
  title,
  url,
  message,
  onClose,
}: DocumentPreviewModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="flex max-h-[90vh] w-full max-w-4xl flex-col rounded-lg bg-card shadow-lg">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="truncate text-sm font-semibold">{title}</h2>
          <Button variant="ghost" size="icon-sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="min-h-[50vh] flex-1 overflow-auto p-4">
          {message ? (
            <p className="text-sm text-muted-foreground">{message}</p>
          ) : url ? (
            <iframe src={url} title={title} className="h-[70vh] w-full rounded border" />
          ) : null}
        </div>
      </div>
    </div>
  );
}
