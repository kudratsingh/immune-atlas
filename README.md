# Immune Atlas

Analysis pipeline and interactive dashboard for immune cell population counts
from a clinical trial dataset. The pipeline loads `data/cell-count.csv` into a
normalised SQLite database, computes per-sample relative frequencies for five
populations (B cells, CD8 T cells, CD4 T cells, NK cells, monocytes), compares
responders with non-responders among melanoma patients treated with miraclib,
and characterises the baseline treatment cohort. The dashboard presents the
results with the statistics attached to every claim.

**Dashboard: <https://kudratsingh.github.io/immune-atlas/>** — deployed from
`main` on every merge, rendering the same committed data bundle that CI
byte-verifies.

## Running it (GitHub Codespaces or local)

```
make setup       # Python and Node dependencies
make pipeline    # database → tables → statistics → plots → dashboard data
make dashboard   # dashboard on port 3000 (binds 0.0.0.0, so Codespaces forwards it)
```

`python load_data.py` on its own creates `cell_counts.db` in the repository
root from the CSV, with no arguments. `make pipeline` runs it and then
`python -m immune_atlas.pipeline`, which regenerates everything under
`outputs/` and `dashboard/public/data/bundle.json`. All input and generated
files are committed, and every data file except the run report is
byte-identical across runs — CI regenerates them and fails on any diff.

`make test` runs both test suites with coverage; `make lint` runs Ruff, mypy,
ESLint, and the TypeScript compiler; `make check` is both, and is the gate CI
applies to every pull request.

## Findings, briefly

Across 1,968 PBMC samples from 656 melanoma patients on miraclib (331
responders, 325 non-responders):

- CD4 T cells are the only population whose relative frequency differs between
  responders and non-responders at unadjusted p < 0.05 (Mann–Whitney U,
  p ≈ 0.013, responders higher: median 30.2% vs 29.7%). After
  Benjamini–Hochberg adjustment across the five populations it does not clear
  q < 0.05 (q ≈ 0.067), so it is reported as suggestive, not significant.
- Each subject contributes three samples (days 0, 7, 14) while response is a
  subject-level label, so per-sample tests overstate independence. The
  per-subject sensitivity analysis (one averaged value per subject) agrees:
  CD4 T cells at p ≈ 0.012, nothing else below 0.10.
- Stratified by time point, no population differs at baseline; CD4 T cells
  separate at day 7 and B cells at day 14. Whatever signal exists appears
  after treatment starts — a response indicator rather than a baseline
  predictor, which matters for the stated aim of predicting response.

The full table, plots, and caveats are in
[outputs/response_comparison.md](outputs/response_comparison.md) and on the
dashboard's Response page. The baseline cohort (melanoma, miraclib, PBMC,
day 0) holds 656 samples from 656 subjects: 384 from prj1 and 272 from prj3;
331 responders / 325 non-responders; 344 males / 312 females. The form
question's answer (melanoma males, responders, day 0, all sample and treatment
types) is 10206.15 across 485 samples, computed by the pipeline in
[outputs/form_answer.json](outputs/form_answer.json).

## Database schema

```
projects ─< subjects ─< samples ─< cell_counts >─ cell_populations
```

Five tables: `projects`; `subjects` (condition, age, sex, treatment,
response — everything constant per person); `samples` (type and day, keyed to
a subject); `cell_populations` (the five measured populations with display
names and a fixed order); and `cell_counts` (one row per sample × population).
Two views, `v_sample_totals` and `v_cell_frequencies`, express the Part 2
table in SQL so it can never drift from the counts. Check constraints encode
the data contract (sex, response, non-negative counts), a unique key forbids
duplicate subject/type/day samples, and the loader additionally validates that
subject-level columns are constant per subject — a violation is an error, not
something to average away. `response` is NULL for untreated subjects and is
never coerced to "no".

**Why this shape.** The CSV is a denormalised join of four entities, with
subject metadata repeated on every row and populations as columns. Splitting
the entities removes the duplication, lets the database enforce consistency,
and — the part that matters for scaling — stores counts long. A sixth
population is a row in `cell_populations`, not an `ALTER TABLE`; a new
analytic (trends over time, ratios between populations, panel comparisons) is
a `GROUP BY`, not a schema migration.

**How it scales.** Hundreds of projects are rows behind a foreign key.
Thousands of samples times dozens of populations is a few hundred thousand
narrow rows — trivial for SQLite, and the same DDL runs unchanged on Postgres
when concurrent writers or row-level security become requirements. The indexes
cover the access paths the analytics use (cohort filters on condition and
treatment, population lookups). The first migrations to make if the study
design changed are noted in
[ADR-0001](docs/adr/0001-sqlite-long-format-schema.md): a treatment-course
table if subjects could switch treatments, and lookup tables for condition and
sample type once controlled vocabularies exist.

## Code structure

```
load_data.py           Part 1 entry point: validate the CSV, then rebuild the database
immune_atlas/
  config.py            population names, cohort filters, output columns — defined once
  db/                  schema, validation, loading, and all SQL queries
  analysis/            pure DataFrame → DataFrame functions: frequencies, statistics, plots
  export.py            deterministic writers for every output and the dashboard bundle
  pipeline.py          eight ordered stages with per-stage metrics and a run report
  observability.py     logging, timers, and the metrics behind the provenance page
dashboard/             Next.js (TypeScript, static export); reads one JSON bundle
contracts/             JSON Schema for the pipeline → dashboard bundle
outputs/               generated tables, report, and plots (committed)
tests/                 pytest unit + integration; the dashboard has Vitest + Playwright
docs/                  specification, architecture, ADRs, UX brief, data notes
```

Three layers with one job each. The **data layer** is the only code that
touches SQLite; Part 4's aggregations run as SQL because the assignment asks
the database, not pandas. The **analysis layer** is pure functions over
DataFrames — no I/O, no connections — which is what makes the statistics
testable against ten-row synthetic frames with planted effects. The
**delivery layer** turns results into files and screens: the exporter writes
every output with fixed ordering and float formats, validates the dashboard
bundle against
[its JSON Schema contract](contracts/dashboard-bundle.schema.json) before
writing, and the dashboard renders only that bundle — one static artifact, no
second server, so `make dashboard` starts exactly one process and the hosted
site cannot drift from the repository.

Determinism is enforced rather than promised: CI reruns the pipeline and fails
if any committed data file changes (the SQLite file and PNGs are checked
structurally instead, since their bytes vary with library builds). Statistical
choices — why Mann–Whitney U, why Benjamini–Hochberg, why the per-subject and
per-time companions are required — are recorded in
[ADR-0002](docs/adr/0002-response-comparison-statistics.md), and the
dashboard's Methods page carries the same provenance (input checksum, row
counts, library versions) so a sceptical reader can verify without cloning
anything.

## Tests

```
make test                             # pytest (90% coverage gate) + Vitest (80% gate)
make check                            # the CI gate: lint + types + all tests
npm --prefix dashboard run test:e2e   # Playwright against the static build
```

Integration tests run the real pipeline on the real CSV into a temporary
directory and assert the reference numbers above (cohort sizes, p-values, the
form answer); a determinism test runs it twice and compares bytes. Playwright
asserts the same key numbers appear on each dashboard route.

## Documentation

- [docs/SPEC.md](docs/SPEC.md) — the assignment and the acceptance checklist
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — schema, pipeline, bundle contract, dashboard
- [docs/adr/](docs/adr/README.md) — decision records (schema, statistics, dashboard stack, pipeline, testing, observability, hosting)
- [docs/DASHBOARD_UX.md](docs/DASHBOARD_UX.md) — personas, information architecture, visual direction
- [docs/DATA_NOTES.md](docs/DATA_NOTES.md) — dataset profile and reference numbers
- [docs/PLAN.md](docs/PLAN.md) — workstreams and status
- [CONTRIBUTING.md](CONTRIBUTING.md) — branching, commits, review
