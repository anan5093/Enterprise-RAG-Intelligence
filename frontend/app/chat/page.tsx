"use client";

import { Bot, Braces, FileText, LockKeyhole, Search, Send, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import { ConfidenceBar } from "@/components/ConfidenceBar";
import { DashboardPanel } from "@/components/DashboardPanel";
import { IntelligenceCard } from "@/components/IntelligenceCard";
import { MetricCard } from "@/components/MetricCard";
import { Shell } from "@/components/Shell";
import { TracePanel } from "@/components/TracePanel";
import { queryRag } from "@/lib/api";
import { getPrincipal, getToken } from "@/lib/session";
import type { QueryResponse } from "@/types/rag";
import { useRouter } from "next/navigation";

export default function ChatPage() {
  const router = useRouter();
  const [query, setQuery] = useState("Show critical security alerts");
  const [answer, setAnswer] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const principal = typeof window !== "undefined" ? getPrincipal() : null;

  async function submit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return router.replace("/login");
    setLoading(true);
    setError("");
    try {
      setAnswer(await queryRag(token, query));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthGuard>
      <Shell>
        <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[minmax(0,1fr)_390px]">
          <section className="min-w-0 px-4 py-5 sm:px-6 lg:px-8">
            <header className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
              <div>
                <div className="inline-flex items-center gap-2 rounded border border-mint/25 bg-mint/10 px-3 py-1.5 text-xs font-medium text-mint">
                  <Sparkles className="h-3.5 w-3.5" />
                  Enterprise AI intelligence workspace
                </div>
                <h1 className="mt-4 text-3xl font-semibold tracking-tight text-paper sm:text-4xl">Grounded retrieval assistant</h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-paper/50">
                  Ask cross-source questions with RBAC-filtered retrieval, cited answers, confidence scoring, and traceable evidence.
                </p>
              </div>
              <div className="rounded border border-line/75 bg-panel/60 px-4 py-3 text-sm text-paper/60 backdrop-blur">
                {principal?.username || "user"} · {principal?.clearance || "authorized"}
              </div>
            </header>

            <div className="mb-6 grid gap-4 md:grid-cols-3">
              <MetricCard label="Security" value="RBAC" detail="Context filtered before generation" icon={LockKeyhole} tone="mint" />
              <MetricCard label="Retrieval" value={answer ? String(answer.trace.candidate_chunk_ids.length) : "Ready"} detail="Hybrid semantic evidence pipeline" icon={Search} tone="cyan" />
              <MetricCard label="Citations" value={answer ? String(answer.citations.length) : "0"} detail="Source-backed answer provenance" icon={FileText} tone="amber" />
            </div>

            <DashboardPanel
              eyebrow="Query"
              title="Ask the enterprise knowledge graph"
              action={<div className="hidden rounded border border-line bg-ink/70 px-3 py-1.5 text-xs text-paper/40 sm:block">FAISS · RBAC · Citations</div>}
            >
              <form onSubmit={submit} className="space-y-4">
                <textarea
                  className="focus-ring min-h-[132px] w-full resize-none rounded border border-line/80 bg-[#0c0f15] px-4 py-4 text-sm leading-6 text-paper shadow-inner shadow-black/20 outline-none placeholder:text-paper/30 focus:border-mint/70"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask about incidents, policies, controls, logs, or reports..."
                />
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="text-xs text-paper/40">Unauthorized sources are excluded before the model sees context.</div>
                  <button
                    className="focus-ring flex h-11 items-center justify-center gap-2 rounded bg-mint px-5 text-sm font-semibold text-ink shadow-[0_14px_44px_rgba(123,220,181,0.18)] transition hover:bg-[#8de6c3] disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={loading}
                  >
                    <Send className="h-4 w-4" />
                    {loading ? "Retrieving..." : "Run secure query"}
                  </button>
                </div>
              </form>
            </DashboardPanel>

            {error ? <div className="mt-5 rounded border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral">{error}</div> : null}

            <div className="mt-6 space-y-6">
              {answer ? (
                <>
                  <IntelligenceCard>
                    <div className="border-b border-line/75 px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="grid h-9 w-9 place-items-center rounded border border-mint/30 bg-mint/10">
                          <Bot className="h-4 w-4 text-mint" />
                        </div>
                        <div>
                          <div className="text-sm font-semibold">Grounded answer</div>
                          <div className="text-xs text-paper/40">Generated from authorized retrieved evidence</div>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-5 p-5">
                      <div className="whitespace-pre-wrap text-base leading-8 text-paper/90">{answer.answer}</div>
                      <ConfidenceBar value={answer.confidence} />
                    </div>
                  </IntelligenceCard>

                  <DashboardPanel eyebrow="Sources" title="Citation set">
                    <div className="grid gap-3 md:grid-cols-2">
                      {answer.citations.map((citation, index) => (
                        <div key={citation.chunk_id} className="rounded border border-line/75 bg-ink/40 p-4 transition hover:border-mint/30 hover:bg-panel/70">
                          <div className="mb-3 flex items-center justify-between gap-3">
                            <span className="rounded border border-mint/20 bg-mint/10 px-2 py-1 text-xs text-mint">#{index + 1}</span>
                            <span className="font-mono text-[11px] text-paper/30">{citation.score?.toFixed(3) ?? "n/a"}</span>
                          </div>
                          <div className="font-medium text-paper">{citation.source}</div>
                          <div className="mt-2 flex flex-wrap gap-2 text-xs text-paper/40">
                            {citation.page ? <span>Page {citation.page}</span> : null}
                            {citation.table ? <span>Table {citation.table}</span> : null}
                            {citation.row_id ? <span>Row {citation.row_id}</span> : null}
                          </div>
                          <div className="mt-3 flex items-center gap-2 font-mono text-[11px] text-paper/30">
                            <Braces className="h-3.5 w-3.5" />
                            {citation.chunk_id}
                          </div>
                        </div>
                      ))}
                    </div>
                  </DashboardPanel>
                </>
              ) : (
                <DashboardPanel>
                  <div className="grid min-h-[220px] place-items-center text-center">
                    <div>
                      <div className="mx-auto grid h-14 w-14 place-items-center rounded border border-line bg-ink">
                        <Bot className="h-6 w-6 text-mint" />
                      </div>
                      <h2 className="mt-4 text-lg font-semibold">Ready for secure retrieval</h2>
                      <p className="mt-2 max-w-lg text-sm leading-6 text-paper/50">
                        Submit a query to see answer synthesis, citations, confidence, and the full explainability trace.
                      </p>
                    </div>
                  </div>
                </DashboardPanel>
              )}
            </div>
          </section>

          <div className="hidden xl:block">
            {answer ? <TracePanel trace={answer.trace} /> : <TracePlaceholder />}
          </div>
        </div>
      </Shell>
    </AuthGuard>
  );
}

function TracePlaceholder() {
  return (
    <aside className="h-full border-l border-line/80 bg-[#10141b]/90 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-mint/75">Explainability</div>
      <h2 className="mt-1 text-lg font-semibold">Trace console</h2>
      <p className="mt-2 text-sm leading-6 text-paper/50">Retrieval routing, RBAC filtering, latency, and provenance appear after a query.</p>
    </aside>
  );
}
