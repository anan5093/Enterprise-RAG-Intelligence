"use client";

import { Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { ConfidenceBar } from "@/components/ConfidenceBar";
import { Shell } from "@/components/Shell";
import { TracePanel } from "@/components/TracePanel";
import { queryRag } from "@/lib/api";
import { getPrincipal, getToken } from "@/lib/session";
import type { QueryResponse } from "@/types/rag";
import { useRouter } from "next/navigation";

export default function ChatPage() {
  const router = useRouter();
  const [query, setQuery] = useState("Summarize Q4 finance compliance findings");
  const [answer, setAnswer] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const principal = typeof window !== "undefined" ? getPrincipal() : null;

  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, [router]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const token = getToken();
    if (!token) return router.push("/login");
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
    <Shell>
      <div className="grid min-h-[calc(100vh-57px)] grid-cols-[minmax(0,1fr)_360px]">
        <section className="flex flex-col">
          <div className="border-b border-line px-6 py-4">
            <div className="text-sm text-paper/60">{principal?.username} · {principal?.clearance}</div>
            <h1 className="mt-1 text-2xl font-semibold">Grounded Enterprise Query</h1>
          </div>
          <div className="flex-1 space-y-5 overflow-auto p-6">
            {answer ? (
              <div className="max-w-4xl space-y-5">
                <div className="whitespace-pre-wrap text-base leading-7">{answer.answer}</div>
                <ConfidenceBar value={answer.confidence} />
                <div>
                  <h2 className="mb-2 text-sm font-semibold">Sources</h2>
                  <div className="grid gap-2">
                    {answer.citations.map((citation) => (
                      <div key={citation.chunk_id} className="rounded border border-line bg-panel p-3 text-sm">
                        <span className="font-mono text-xs text-mint">{citation.chunk_id}</span>
                        <span className="ml-2">{citation.source}</span>
                        {citation.page ? <span className="ml-2 text-paper/60">page {citation.page}</span> : null}
                        {citation.table ? <span className="ml-2 text-paper/60">table {citation.table}</span> : null}
                      </div>
                    ))}
                    {!answer.citations.length ? <div className="text-sm text-paper/60">No authorized citations returned.</div> : null}
                  </div>
                </div>
                <p className="text-sm text-paper/60">{answer.access_filter_explanation}</p>
              </div>
            ) : (
              <div className="max-w-2xl text-paper/60">Ask a question. The backend routes, filters, retrieves, reranks, and only then generates from authorized evidence.</div>
            )}
            {error ? <pre className="whitespace-pre-wrap text-sm text-coral">{error}</pre> : null}
          </div>
          <form onSubmit={submit} className="flex gap-3 border-t border-line p-4">
            <textarea className="focus-ring min-h-12 flex-1 resize-none rounded border border-line bg-panel px-3 py-3" value={query} onChange={(event) => setQuery(event.target.value)} />
            <button className="focus-ring grid h-12 w-12 place-items-center rounded bg-mint text-ink" disabled={loading} title="Send query">
              <Send className="h-5 w-5" />
            </button>
          </form>
        </section>
        {answer ? <TracePanel trace={answer.trace} /> : <aside className="border-l border-line bg-panel/60 p-4 text-sm text-paper/60">Trace appears after a query.</aside>}
      </div>
    </Shell>
  );
}

