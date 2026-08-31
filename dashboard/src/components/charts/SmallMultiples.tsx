import type { ReactNode } from "react";

export function SmallMultiples({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="small-multiples" role="group" aria-label={label}>
      {children}
    </div>
  );
}
