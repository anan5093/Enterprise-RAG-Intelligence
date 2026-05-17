import type { RetrievalTrace } from "@/types/rag";

export function TracePanel({ trace }: { trace: RetrievalTrace }) {
  return (
    <aside className="border-l border-line bg-panel/60 p-4">
      <h2 className="text-sm font-semibold">Retrieval Trace</h2>
      <dl className="mt-4 space-y-3 text-sm">
        <div>
          <dt className="text-paper/50">Route</dt>
          <dd>{trace.route.query_type} / {trace.route.strategy}</dd>
        </div>
        <div>
          <dt className="text-paper/50">Sources</dt>
          <dd>{trace.route.sources.join(", ")}</dd>
        </div>
        <div>
          <dt className="text-paper/50">Latency</dt>
          <dd>{Math.round(trace.latency_ms)} ms</dd>
        </div>
        <div>
          <dt className="text-paper/50">Authorized Chunks</dt>
          <dd className="font-mono text-xs">{trace.authorized_chunk_ids.join(", ") || "none"}</dd>
        </div>
        <div>
          <dt className="text-paper/50">Denied Count</dt>
          <dd>{trace.denied_chunk_ids.length}</dd>
        </div>
      </dl>
      <div className="mt-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-paper/50">Filters</h3>
        <ul className="mt-2 space-y-2 text-xs text-paper/70">
          {trace.filters_applied.slice(0, 6).map((filter) => <li key={filter}>{filter}</li>)}
        </ul>
      </div>
    </aside>
  );
}

