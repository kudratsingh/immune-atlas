import type { ReactNode } from "react";

export function PageIntro({ title, children }: { title: string; children: ReactNode }) {
  return (
    <header className="page-intro">
      <h1>{title}</h1>
      <div>{children}</div>
    </header>
  );
}
