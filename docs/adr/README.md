# Architecture decision records

One file per decision, numbered in the order taken. A record is never edited once
accepted except to change its status; a reversal gets a new record that supersedes
it.

| # | Title | Status |
| - | ----- | ------ |
| 0001 | [Normalised SQLite schema with long-format counts](0001-sqlite-long-format-schema.md) | Accepted |
| 0002 | [Statistical method for the responder comparison](0002-response-comparison-statistics.md) | Accepted |
| 0003 | [Dashboard as a static Next.js app over a pipeline-emitted data bundle](0003-dashboard-static-bundle.md) | Accepted |
| 0004 | [Pipeline orchestration, outputs, and determinism](0004-pipeline-and-outputs.md) | Accepted |
| 0005 | [Testing and CI strategy](0005-testing-and-ci.md) | Accepted |
| 0006 | [Logging and metrics without a running service](0006-observability.md) | Accepted |

Template:

```
# NNNN. Title

Status: Proposed | Accepted | Superseded by NNNN
Date: YYYY-MM-DD

## Context
## Decision
## Alternatives considered
## Consequences
```
