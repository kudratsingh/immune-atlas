# Immune Atlas

Analysis pipeline and interactive dashboard for immune cell population counts
from a clinical trial dataset. The pipeline loads `data/cell-count.csv` into a
normalised SQLite database, computes per-sample relative frequencies for five
populations (B cells, CD8 T cells, CD4 T cells, NK cells, monocytes), compares
responders with non-responders among melanoma patients treated with miraclib,
and characterises the baseline treatment cohort. The dashboard presents the
results with the statistics attached to every claim.

> Status: the implementation is in progress against [docs/PLAN.md](docs/PLAN.md).
> This README is completed in the final workstream; the sections below describe
> the intended shape so the repository is navigable in the meantime.

## Quick start (GitHub Codespaces or local)

```
make setup       # Python and Node dependencies
make pipeline    # database → tables → statistics → plots → dashboard data
make dashboard   # dashboard on http://localhost:3000
```

`python load_data.py` alone creates `cell_counts.db` from the CSV. `make test`
runs the Python and dashboard test suites; `make check` adds lint and
type-checking and is the gate CI applies to every pull request.

Hosted dashboard: _link added on deployment (WS-9)._

## What is where

```
load_data.py      Part 1 entry point — schema + load, no arguments
immune_atlas/     Python package: db/ (schema, validation, loader, queries),
                  analysis/ (frequencies, response statistics, subsets, plots),
                  export.py, pipeline.py, observability.py
dashboard/        Next.js dashboard, reads dashboard/public/data/bundle.json
contracts/        JSON Schema for the pipeline → dashboard bundle
outputs/          Generated tables, report, and plots (committed)
tests/            pytest unit and integration suites
docs/             Specification, data notes, architecture, ADRs, plan, UX brief
```

## Documentation

- [docs/SPEC.md](docs/SPEC.md) — the assignment and the acceptance checklist
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — schema, pipeline, bundle contract, dashboard
- [docs/adr/](docs/adr/README.md) — decision records (schema, statistics, dashboard stack, pipeline, testing, observability)
- [docs/DASHBOARD_UX.md](docs/DASHBOARD_UX.md) — personas, information architecture, visual direction
- [docs/DATA_NOTES.md](docs/DATA_NOTES.md) — dataset profile and reference numbers
- [docs/PLAN.md](docs/PLAN.md) — workstreams and status
- [CONTRIBUTING.md](CONTRIBUTING.md) — branching, commits, review

## Sections to be completed in WS-9

Schema and rationale, including scaling to hundreds of projects and thousands of
samples · Code structure and why · Findings and caveats · Dashboard link ·
Reproducing outputs · Running the tests.
