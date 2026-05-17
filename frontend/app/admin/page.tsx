"use client";

import { Activity, FileClock, LockKeyhole, RefreshCcw, ShieldCheck, TerminalSquare } from "lucide-react";
import { useState } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import { DashboardPanel } from "@/components/DashboardPanel";
import { MetricCard } from "@/components/MetricCard";
import { Shell } from "@/components/Shell";
import { getAuditLogs } from "@/lib/api";
import { getToken } from "@/lib/session";

type AuditEvent = {
  event_type?: string;
  timestamp?: string;
  payload?: {
    confidence?: number;
    denied_count?: number;
    query?: string;
  };
  principal?: {
    username?: string;
  };
};

export default function AdminPage() {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [error, setError] = useState("");

  async function refresh() {
    const token = getToken();
    if (!token) return;
    try {
      setLogs(await getAuditLogs(token));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load audit logs");
    }
  }

  const queryCount = logs.filter((item) => item.event_type === "query").length;
  const ingestCount = logs.filter((item) => item.event_type === "ingest").length;
  const deniedCount = logs.reduce((sum, item) => sum + (item.payload?.denied_count || 0), 0);

  return (
    <AuthGuard>
      <Shell>
        <section className="px-4 py-5 sm:px-6 lg:px-8">
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded border border-mint/25 bg-mint/10 px-3 py-1.5 text-xs font-medium text-mint">
                <ShieldCheck className="h-3.5 w-3.5" />
                Governance console
              </div>
              <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">Security operations dashboard</h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-paper/50">
                Monitor RAG usage, RBAC access decisions, ingestion events, and audit activity across the enterprise assistant.
              </p>
            </div>
            <button onClick={refresh} className="focus-ring flex h-11 items-center justify-center gap-2 rounded bg-mint px-4 text-sm font-semibold text-ink shadow-[0_14px_44px_rgba(123,220,181,0.18)] transition hover:bg-[#8de6c3]">
              <RefreshCcw className="h-4 w-4" />
              Refresh audit stream
            </button>
          </header>

          <div className="grid gap-4 md:grid-cols-4">
            <MetricCard label="Queries" value={String(queryCount)} detail="Authorized assistant requests" icon={Activity} tone="mint" />
            <MetricCard label="Ingestions" value={String(ingestCount)} detail="Indexed enterprise sources" icon={FileClock} tone="cyan" />
            <MetricCard label="Denied chunks" value={String(deniedCount)} detail="Filtered before generation" icon={LockKeyhole} tone="coral" />
            <MetricCard label="Mode" value="Secure" detail="JWT + RBAC active" icon={ShieldCheck} tone="amber" />
          </div>

          {error ? <div className="mt-5 rounded border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral">{error}</div> : null}

          <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
            <DashboardPanel eyebrow="Audit" title="Activity center">
              <div className="space-y-3">
                {logs.slice().reverse().slice(0, 12).map((event, index) => (
                  <div key={`${event.timestamp}-${index}`} className="rounded border border-line/75 bg-ink/40 p-4 transition hover:border-mint/30 hover:bg-panel/60">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <div className="text-sm font-semibold text-paper">{event.event_type || "event"}</div>
                        <div className="mt-1 text-xs text-paper/40">{event.principal?.username || "system"} · {event.timestamp || "pending"}</div>
                      </div>
                      {typeof event.payload?.confidence === "number" ? (
                        <span className="rounded border border-mint/20 bg-mint/10 px-2 py-1 text-xs text-mint">{Math.round(event.payload.confidence * 100)}% confidence</span>
                      ) : null}
                    </div>
                    {event.payload?.query ? <div className="mt-3 text-sm leading-6 text-paper/60">{event.payload.query}</div> : null}
                  </div>
                ))}
                {!logs.length ? <div className="rounded border border-line/75 bg-ink/40 p-8 text-center text-sm text-paper/50">Refresh to load audit activity.</div> : null}
              </div>
            </DashboardPanel>

            <DashboardPanel eyebrow="Controls" title="Enterprise posture">
              <div className="space-y-4">
                <ControlRow label="Authentication" value="JWT active" />
                <ControlRow label="Authorization" value="RBAC metadata filters" />
                <ControlRow label="Generation" value="Grounded citations" />
                <ControlRow label="Observability" value="Audit log stream" />
              </div>
              <div className="mt-5 rounded border border-line/75 bg-ink/40 p-4">
                <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                  <TerminalSquare className="h-4 w-4 text-mint" />
                  Raw audit preview
                </div>
                <pre className="max-h-[340px] overflow-auto whitespace-pre-wrap text-xs leading-5 text-paper/50">{JSON.stringify(logs.slice(-4), null, 2)}</pre>
              </div>
            </DashboardPanel>
          </div>
        </section>
      </Shell>
    </AuthGuard>
  );
}

function ControlRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded border border-line/70 bg-ink/40 px-3 py-3">
      <span className="text-sm text-paper/50">{label}</span>
      <span className="text-right text-sm font-medium text-paper">{value}</span>
    </div>
  );
}
