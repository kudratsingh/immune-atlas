# 0003. Dashboard as a static Next.js app over a pipeline-emitted data bundle

Status: Accepted (hosting superseded by ADR-0007)
Date: 2026-08-30

## Context

The assignment requires an interactive dashboard, started by `make dashboard` in
a GitHub Codespace, and a public link to it in the README. No stack is prescribed.
The dataset is small (10,500 samples) and changes only when the pipeline runs.

## Decision

- **Next.js (App Router, TypeScript, Tailwind, Visx)** built with
  `output: "export"`, so the result is static files.
- The dashboard's only data source is `dashboard/public/data/bundle.json`,
  written by the pipeline's export stage and validated against
  `contracts/dashboard-bundle.schema.json`. TypeScript types are generated from
  that schema.
- Interactivity (filters, sorting, toggling per-sample/per-subject views, hover
  detail) is client-side over the bundle.
- Hosting: Vercel, root directory `dashboard/`, building from `main`.
  `make dashboard` runs `next dev` on `0.0.0.0:3000` against the same bundle.

## Alternatives considered

- **FastAPI serving SQLite + Next.js frontend.** A more conventional full-stack
  shape and a good fit for a live database. Rejected here because it doubles the
  processes `make dashboard` must start, forces a proxy so the browser only talks
  to one forwarded Codespaces port, and needs a separately hosted backend for the
  README link — the most common way for a take-home demo link to be dead on
  review day. It adds no capability at this data volume; every query the API
  would answer is a filter over a few thousand rows.
- **Streamlit or Dash.** Pure Python, minimal effort, and a stated non-goal: the
  brief asks for a deliberately designed, product-quality interface, which those
  frameworks resist.
- **Next.js API routes reading SQLite.** Single process, but puts a second copy
  of the query logic in TypeScript or a native SQLite binding on the serverless
  host; the JSON bundle keeps the Python package the single source of truth.

## Consequences

- One process locally, zero infrastructure remotely, and the public link cannot
  go stale independently of the code.
- The bundle contract is the interface between two workstreams that run in
  parallel; changing it requires a schema change, a regenerated types file, and
  both sides updated in the same PR.
- The pipeline writes into `dashboard/public/data/`. That path is the one place
  the pipeline reaches across a layer boundary, and it is documented as such.
- If the data grew large enough that a full bundle became slow to load, the
  exporter would split it per route; the frontend already loads through one
  module so that change would be local.
