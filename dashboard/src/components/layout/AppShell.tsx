"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const routes = [
  { href: "/", label: "Overview", description: "Dataset shape and analysis questions" },
  { href: "/samples/", label: "Samples", description: "Cell frequency in every sample" },
  { href: "/response/", label: "Response", description: "Responders compared with non-responders" },
  { href: "/baseline/", label: "Baseline", description: "Day-0 miraclib cohort" },
  { href: "/methods/", label: "Methods", description: "Statistics and provenance" },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="topbar">
        <div className="topbar-inner">
          <Link className="wordmark" href="/" aria-label="Immune Atlas overview">
            Immune Atlas
          </Link>
          <nav aria-label="Primary navigation">
            <ul className="nav-list">
              {routes.map((route) => {
                const active =
                  route.href === "/" ? pathname === "/" : pathname.startsWith(route.href);
                return (
                  <li key={route.href}>
                    <Link
                      href={route.href}
                      aria-current={active ? "page" : undefined}
                      title={route.description}
                    >
                      {route.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      </header>
      <main id="main-content" className="page-shell">
        {children}
      </main>
      <footer className="site-footer">
        <div>Immune cell population analysis from a versioned, reproducible data bundle.</div>
      </footer>
    </>
  );
}
