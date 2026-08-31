# 0004. Pipeline orchestration, outputs, and determinism

Status: Accepted
Date: 2026-08-30

## Context

`make pipeline` must run everything from database initialisation through plots
without intervention, in a Codespace, and the generated files are part of the
submission. The assignment allows any orchestrator.

## Decision

- Orchestration is a plain Python module (`immune_atlas/pipeline.py`) with an
  ordered list of stage functions and a shared context. `make pipeline` calls
  `python load_data.py` followed by `python -m immune_atlas.pipeline`.
- Every generated data file is deterministic for a given input: fixed sort
  orders, fixed float formats, no timestamps in tables. CI runs the pipeline and
  fails if `git diff` shows changes in `outputs/` (tables, report, JSON) or the
  dashboard bundle. The SQLite file and the PNG plots are excluded from the
  byte-level check because their bytes depend on the SQLite and matplotlib
  builds; the integration tests verify them structurally (row counts and schema
  for the database, valid PNG with fixed dimensions for the plots) and the
  determinism test verifies byte-identity within one environment.
- Generated files are committed. The database (≈ 2 MB) is included because the
  assignment asks for generated outputs and because it lets a reviewer open the
  schema without running anything.
- The pipeline rebuilds from scratch every run. There is no incremental mode; at
  a few seconds of runtime, caching would only add ways to be stale.

## Alternatives considered

- **Snakemake / Makefile rules per output.** Real dependency tracking, but a
  second DSL for a linear eight-stage flow, and Snakemake is a heavy install for
  a Codespace.
- **Not committing the database.** Cleaner history, but the grader may read
  before running and the file is small and byte-stable.
- **Timestamps in outputs.** Useful provenance, fatal for the determinism check;
  provenance goes in `outputs/pipeline_run.json`, which is excluded from the diff
  check and carries the input checksum instead.

## Consequences

- Reproducibility is enforced by CI, not promised in prose.
- A stage failure exits non-zero with the stage name; partial outputs from a
  failed run are not committed by construction (CI fails).
