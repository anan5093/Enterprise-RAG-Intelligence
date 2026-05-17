"use client";

import { RefreshCcw } from "lucide-react";
import { useState } from "react";
import { Shell } from "@/components/Shell";
import { getAuditLogs } from "@/lib/api";
import { getToken } from "@/lib/session";

type AuditEvent = {
  event_type?: string;
  timestamp?: string;
  payload?: unknown;
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

  return (
    <Shell>
      <section className="p-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Admin Dashboard</h1>
          <button onClick={refresh} className="focus-ring flex items-center gap-2 rounded border border-line px-3 py-2 text-sm">
            <RefreshCcw className="h-4 w-4" />
            Refresh
          </button>
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-4">
          <Metric label="Queries" value={String(logs.filter((item) => item.event_type === "query").length)} />
          <Metric label="Ingestions" value={String(logs.filter((item) => item.event_type === "ingest").length)} />
          <Metric label="Access Checks" value="pre-LLM" />
          <Metric label="Mode" value="secure" />
        </div>
        {error ? <p className="mt-4 text-sm text-coral">{error}</p> : null}
        <pre className="mt-6 max-h-[520px] overflow-auto rounded border border-line bg-panel p-4 text-xs">{JSON.stringify(logs, null, 2)}</pre>
      </section>
    </Shell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-line bg-panel p-4">
      <div className="text-xs uppercase tracking-wide text-paper/50">{label}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}
