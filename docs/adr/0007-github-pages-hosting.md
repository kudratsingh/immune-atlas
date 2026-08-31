# 0007. Host the dashboard on GitHub Pages

Status: Accepted (supersedes the hosting clause of ADR-0003)
Date: 2026-08-31

## Context

ADR-0003 committed to a static Next.js export and named Vercel as the host. The
build produces plain static files, so the only real requirements on the host are
that it serves them publicly and that the published link cannot rot separately
from the repository.

## Decision

Deploy the static export to GitHub Pages from a repository workflow
(`.github/workflows/deploy.yml`) on every push to `main`. The site lives under
`/immune-atlas/`, so the Pages build injects `NEXT_PUBLIC_BASE_PATH=/immune-atlas`;
`next.config.ts` applies it as `basePath` and the bundle loader prefixes its one
fetch with it. Local development, `make dashboard`, Codespaces, CI, and the
Playwright suite build without the variable and are unchanged.

## Alternatives considered

- **Vercel (ADR-0003).** Equivalent output, nicer preview deployments per PR.
  Requires a second account and a token held outside the repository; the
  deployment then depends on state that a reviewer cannot see. Pages keeps the
  entire deployment inside the repository.
- **Serving from the `pipeline` CI artifact.** Not publicly routable.

## Consequences

- The README links to `https://kudratsingh.github.io/immune-atlas/`.
- The dashboard updates automatically when a pull request merges; the deployed
  bundle is exactly the committed one, which CI has already byte-verified.
- Per-PR preview deployments are given up; the Playwright suite covers the
  routes instead.
