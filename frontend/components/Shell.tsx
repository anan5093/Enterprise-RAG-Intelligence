"use client";

import { Database, FileUp, LayoutDashboard, LogOut, MessageSquare } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearSession, getPrincipal } from "@/lib/session";

const nav = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/upload", label: "Upload", icon: FileUp },
  { href: "/admin", label: "Admin", icon: LayoutDashboard },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const principal = typeof window !== "undefined" ? getPrincipal() : null;

  return (
    <main className="min-h-screen bg-ink text-paper">
      <header className="flex items-center justify-between border-b border-line px-5 py-3">
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-mint" />
          <div>
            <div className="text-sm font-semibold">Enterprise Secure RAG</div>
            <div className="text-xs text-paper/60">{principal?.roles.join(", ") || "Unauthenticated"}</div>
          </div>
        </div>
        <nav className="flex items-center gap-1">
          {nav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`focus-ring flex h-9 items-center gap-2 rounded px-3 text-sm ${active ? "bg-paper text-ink" : "text-paper/70 hover:bg-panel"}`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
          <button
            className="focus-ring ml-2 flex h-9 items-center gap-2 rounded border border-line px-3 text-sm text-paper/80"
            onClick={() => {
              clearSession();
              router.push("/login");
            }}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </nav>
      </header>
      {children}
    </main>
  );
}

