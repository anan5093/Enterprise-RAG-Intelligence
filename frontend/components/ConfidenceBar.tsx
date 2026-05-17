export function ConfidenceBar({ value }: { value: number }) {
  const percent = Math.round(value * 100);
  const label = value > 0.75 ? "High trust" : value > 0.5 ? "Moderate trust" : "Low trust";
  return (
    <div className="w-full rounded border border-line/75 bg-ink/40 p-4 shadow-inner shadow-black/20">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.16em] text-paper/40">AI confidence</div>
          <div className="mt-1 text-sm font-medium text-paper">{label}</div>
        </div>
        <div className="rounded border border-mint/25 bg-mint/10 px-3 py-1 font-mono text-sm text-mint">{percent}%</div>
      </div>
      <div className="h-2.5 overflow-hidden rounded bg-line">
        <div
          className="h-full rounded bg-gradient-to-r from-coral via-amber to-mint shadow-[0_0_22px_rgba(123,220,181,0.22)] transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="mt-2 text-xs text-paper/40">Calibrated from retrieval quality, evidence coverage, and source agreement.</div>
    </div>
  );
}
