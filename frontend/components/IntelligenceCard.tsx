import type { ReactNode } from "react";

export function IntelligenceCard({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded border border-line/75 bg-[#11151c]/78 shadow-xl shadow-black/20 backdrop-blur-xl ${className}`}>
      {children}
    </div>
  );
}
