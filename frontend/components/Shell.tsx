"use client";

import { BrainCircuit, Database, FileUp, LayoutDashboard, LogOut, MessageSquare, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearSession, getPrincipal } from "@/lib/session";

const nav = [
  { href: "/chat", label: "Intelligence", icon: MessageSquare },
  { href: "/upload", label: "Ingestion", icon: FileUp },
  { href: "/admin", label: "Governance", icon: LayoutDashboard },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const principal = typeof window !== "undefined" ? getPrincipal() : null;

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0b0d12] text-paper">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.028)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.028)_1px,transparent_1px)] bg-[size:48px_48px]" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(135deg,rgba(123,220,181,0.09),transparent_32%,rgba(244,184,96,0.06)_72%,transparent)]" />

      <div className="relative z-10 grid min-h-screen grid-cols-1 lg:grid-cols-[272px_minmax(0,1fr)]">
        <aside className="hidden border-r border-line/80 bg-[#10141b]/90 p-4 shadow-2xl shadow-black/30 backdrop-blur-xl lg:flex lg:flex-col">
          <div className="flex items-center gap-3 px-2 py-3">
            <div className="grid h-11 w-11 place-items-center rounded border border-mint/30 bg-mint/10 shadow-[0_0_28px_rgba(123,220,181,0.13)]">
              <BrainCircuit className="h-5 w-5 text-mint" />
            </div>
            <div>
              <div className="text-sm font-semibold">Enterprise RAG</div>
              <div className="text-xs text-paper/40">Secure AI Console</div>
            </div>
          </div>

          <nav className="mt-7 space-y-2">
            {nav.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`focus-ring flex h-11 items-center gap-3 rounded px-3 text-sm transition ${
                    active
                      ? "border border-mint/30 bg-mint/10 text-mint shadow-[0_0_24px_rgba(123,220,181,0.10)]"
                      : "border border-transparent text-paper/60 hover:border-line hover:bg-panel/60 hover:text-paper"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto rounded border border-line/75 bg-panel/50 p-4">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded border border-line bg-ink">
                <Database className="h-4 w-4 text-mint" />
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">{principal?.username || "Session"}</div>
                <div className="truncate text-xs text-paper/40">{principal?.roles.join(", ") || "Unauthenticated"}</div>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 rounded border border-mint/20 bg-mint/10 px-3 py-2 text-xs text-mint/80">
              <ShieldCheck className="h-4 w-4" />
              RBAC pre-filtering active
            </div>
            <button
              className="focus-ring mt-3 flex h-10 w-full items-center justify-center gap-2 rounded border border-line bg-ink/70 text-sm text-paper/70 transition hover:border-coral/40 hover:text-coral"
              onClick={() => {
                clearSession();
                router.replace("/login");
              }}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </aside>

        <section className="min-w-0">
          <header className="flex items-center justify-between border-b border-line/80 bg-[#10141b]/82 px-4 py-3 backdrop-blur-xl lg:hidden">
            <div className="flex items-center gap-2">
              <BrainCircuit className="h-5 w-5 text-mint" />
              <span className="text-sm font-semibold">Enterprise RAG</span>
            </div>
            <button
              className="focus-ring rounded border border-line px-3 py-2 text-xs text-paper/70"
              onClick={() => {
                clearSession();
                router.replace("/login");
              }}
            >
              Sign out
            </button>
          </header>
          <div className="min-h-screen">{children}</div>
        </section>
      </div>
    </main>
  );
}
