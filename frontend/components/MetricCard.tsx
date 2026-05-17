import type { LucideIcon } from "lucide-react";

type MetricCardProps = {
  label: string;
  value: string;
  detail?: string;
  icon: LucideIcon;
  tone?: "mint" | "amber" | "coral" | "cyan";
};

export function MetricCard({ label, value, detail, icon: Icon, tone = "mint" }: MetricCardProps) {
  const tones = {
    mint: "border-mint/30 bg-mint/10 text-mint",
    amber: "border-amber/30 bg-amber/10 text-amber",
    coral: "border-coral/30 bg-coral/10 text-coral",
    cyan: "border-cyan-300/30 bg-cyan-300/10 text-cyan-200",
  };

  return (
    <div className="rounded border border-line/80 bg-panel/60 p-4 shadow-xl shadow-black/20 backdrop-blur transition hover:border-mint/30 hover:bg-panel/80">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.16em] text-paper/40">{label}</div>
          <div className="mt-2 text-2xl font-semibold text-paper">{value}</div>
        </div>
        <div className={`grid h-10 w-10 place-items-center rounded border ${tones[tone]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      {detail ? <div className="mt-3 text-xs leading-5 text-paper/50">{detail}</div> : null}
    </div>
  );
}

