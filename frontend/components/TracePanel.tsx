import type { RetrievalTrace } from "@/types/rag";

export function TracePanel({ trace }: { trace: RetrievalTrace }) {
  const latency = Math.round(trace.latency_ms);
  return (
    <aside className="h-full overflow-auto border-l border-line/80 bg-[#10141b]/90 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl">
      <div className="mb-5">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-mint/75">Explainability</div>
        <h2 className="mt-1 text-lg font-semibold">Retrieval trace</h2>
        <p className="mt-2 text-xs leading-5 text-paper/50">Authorized evidence path before generation.</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <TraceStat label="Latency" value={`${latency}ms`} />
        <TraceStat label="Denied" value={String(trace.denied_chunk_ids.length)} />
        <TraceStat label="Authorized" value={String(trace.authorized_chunk_ids.length)} />
        <TraceStat label="Candidates" value={String(trace.candidate_chunk_ids.length)} />
      </div>

      <div className="mt-5 rounded border border-line/75 bg-ink/40 p-4">
        <div className="text-xs uppercase tracking-[0.16em] text-paper/40">Route</div>
        <div className="mt-2 text-sm font-medium">{trace.route.query_type} · {trace.route.strategy}</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {trace.route.sources.map((source) => (
            <span key={source} className="rounded border border-mint/20 bg-mint/10 px-2 py-1 text-xs text-mint/80">{source}</span>
          ))}
        </div>
      </div>

      <div className="mt-5">
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-paper/40">Evidence timeline</div>
        <div className="mt-3 space-y-3">
          {trace.authorized_chunk_ids.slice(0, 6).map((chunkId, index) => (
            <div key={chunkId} className="flex gap-3">
              <div className="flex flex-col items-center">
                <div className="grid h-6 w-6 place-items-center rounded-full border border-mint/30 bg-mint/10 text-[10px] text-mint">{index + 1}</div>
                {index < Math.min(trace.authorized_chunk_ids.length, 6) - 1 ? <div className="h-6 w-px bg-line" /> : null}
              </div>
              <div className="min-w-0 flex-1 rounded border border-line/70 bg-panel/40 px-3 py-2">
                <div className="truncate font-mono text-xs text-paper/60">{chunkId}</div>
                <div className="mt-1 text-[11px] text-paper/40">Passed RBAC and sensitivity filters</div>
              </div>
            </div>
          ))}
          {!trace.authorized_chunk_ids.length ? <div className="text-sm text-paper/40">No authorized chunks returned.</div> : null}
        </div>
      </div>

      <div className="mt-5 rounded border border-line/75 bg-ink/40 p-4">
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-paper/40">Filters applied</div>
        <ul className="mt-3 space-y-2 text-xs leading-5 text-paper/60">
          {trace.filters_applied.slice(0, 6).map((filter) => <li key={filter}>• {filter}</li>)}
        </ul>
      </div>
    </aside>
  );
}

function TraceStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-line/75 bg-panel/50 p-3">
      <div className="text-[11px] uppercase tracking-[0.14em] text-paper/40">{label}</div>
      <div className="mt-1 font-mono text-lg font-semibold text-paper">{value}</div>
    </div>
  );
}
