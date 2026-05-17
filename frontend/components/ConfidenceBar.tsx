export function ConfidenceBar({ value }: { value: number }) {
  const percent = Math.round(value * 100);
  const color = value > 0.75 ? "bg-mint" : value > 0.5 ? "bg-amber" : "bg-coral";
  return (
    <div className="w-full">
      <div className="mb-1 flex justify-between text-xs text-paper/60">
        <span>Confidence</span>
        <span>{percent}%</span>
      </div>
      <div className="h-2 rounded bg-line">
        <div className={`h-2 rounded ${color}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

