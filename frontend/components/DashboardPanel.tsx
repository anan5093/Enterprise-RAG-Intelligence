import type { ReactNode } from "react";

type DashboardPanelProps = {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function DashboardPanel({ title, eyebrow, action, children, className = "" }: DashboardPanelProps) {
  return (
    <section className={`rounded border border-line/80 bg-panel/70 shadow-[0_24px_80px_rgba(0,0,0,0.26)] backdrop-blur-xl ${className}`}>
      {(title || eyebrow || action) ? (
        <div className="flex items-start justify-between gap-4 border-b border-line/70 px-5 py-4">
          <div>
            {eyebrow ? <div className="text-xs font-semibold uppercase tracking-[0.18em] text-mint/75">{eyebrow}</div> : null}
            {title ? <h2 className="mt-1 text-base font-semibold text-paper">{title}</h2> : null}
          </div>
          {action}
        </div>
      ) : null}
      <div className="p-5">{children}</div>
    </section>
  );
}

