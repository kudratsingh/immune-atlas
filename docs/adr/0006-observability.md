# 0006. Logging and metrics without a running service

Status: Accepted
Date: 2026-08-30

## Context

The pipeline is a batch job that runs for seconds. There is no server to scrape
and no log aggregator. Reviewers still expect to see how a run went, and future
operators would want to know when row counts or durations drift.

## Decision

- Structured logging via the standard library: one logger per module, INFO for
  stage boundaries with row counts and durations, ERROR for contract violations
  with row references. Plain text by default; JSON lines with
  `IMMUNE_ATLAS_LOG_JSON=1` for machine consumption.
- A small `Metrics` collector (counters, gauges, timers keyed by stage) written to
  `outputs/pipeline_run.json` at the end of every run and embedded in the
  dashboard bundle. It records the input checksum, per-stage rows and seconds,
  warnings, and library versions.
- The dashboard's Methods page renders that run report as data provenance.

## Alternatives considered

- **Prometheus client / OpenTelemetry SDK.** Correct for a service; here it would
  add dependencies and an exporter with nothing to receive from it. The `Metrics`
  interface is deliberately the same shape (counter, gauge, timer) so an OTLP
  exporter could be swapped in later.
- **`print` statements.** Not filterable, not structured, and indistinguishable
  from output.

## Consequences

- Every run leaves a machine-readable record next to its outputs.
- The determinism check excludes `pipeline_run.json`, which is the only file that
  legitimately changes between identical runs.
