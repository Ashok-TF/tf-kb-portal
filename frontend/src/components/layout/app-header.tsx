"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpen, LogOut, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { clearSession, getEmail } from "@/lib/api";
import { useEffect, useState } from "react";

export function AppHeader() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    setEmail(getEmail());
  }, []);

  function handleLogout() {
    clearSession();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-10 border-b bg-card/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
            tf
          </div>
          <div className="flex items-center gap-1.5">
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-semibold">KB Portal</span>
          </div>
        </Link>
        <div className="flex items-center gap-2">
          <Link href="/chat">
            <Button variant="ghost" size="sm">
              <MessageSquare className="h-4 w-4 mr-1.5" />
              Chat
            </Button>
          </Link>
          {email && <span className="text-sm text-muted-foreground hidden sm:inline">{email}</span>}
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-1.5" />
            Sign out
          </Button>
        </div>
      </div>
    </header>
  );
}
