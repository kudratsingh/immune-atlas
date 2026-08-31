import type { ReactNode } from "react";

export function PageIntro({
  title,
  motif,
  children,
}: {
  title: string;
  motif?: ReactNode;
  children: ReactNode;
}) {
  return (
    <header className="page-intro">
      <div className="page-intro-inner">
        <div className="page-intro-copy">
          <h1>{title}</h1>
          <div>{children}</div>
        </div>
        {motif ? (
          <div aria-hidden="true" className="page-intro-motif">
            {motif}
          </div>
        ) : null}
      </div>
    </header>
  );
}
