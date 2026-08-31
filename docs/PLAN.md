# Build plan

The plan is organised as workstreams (WS). Each WS section is a complete brief:
it can be handed to one person or agent, worked in its own worktree, and merged
through one PR. The coordinating agent updates the status table as PRs merge.

Status legend: `todo` · `in progress` · `in review` · `done`.

## Dependency graph

```
Phase 0  PLANNING (main, initial commit)
            │
Phase 1  WS-1 Foundation ─────────────────────────────────────────┐
            │                                                     │
Phase 2     ├── WS-2 Data layer ─────┐                            │
            ├── WS-3 Analysis  ──────┤ (parallel; share config.py │
            └── WS-4 Dashboard shell ┘  and the bundle contract)  │
                       │                                          │
Phase 3  WS-5 Pipeline + export (needs WS-2, WS-3) ───────────────┤
            │                                                     │
Phase 4     ├── WS-6 Dashboard: Overview + Samples                │
            ├── WS-7 Dashboard: Response analysis   (parallel;    │
            └── WS-8 Dashboard: Baseline + Methods   need WS-5    │
                       │                             bundle)      │
Phase 5  WS-9 Hardening: e2e, README, deploy, submission check ◄──┘
```

WS-2, WS-3, WS-4 can run at the same time because their interfaces are fixed in
advance: the SQL schema (ARCHITECTURE §Schema), the constants in `config.py`
(created in WS-1), and `contracts/dashboard-bundle.schema.json` (created in WS-1).
WS-4 develops against a fixture bundle that satisfies the schema; WS-3 develops
against synthetic DataFrames.

## Status

| WS | Title | Branch | Owner | Status |
| -- | ----- | ------ | ----- | ------ |
| 0 | Planning docs, repo bootstrap | `main` (initial commit) | coordinator | done |
| 1 | Foundation | `feat/foundation` | coordinator | done |
| 2 | Data layer | `feat/data-layer` | delegate | done |
| 3 | Analysis | `feat/analysis` | delegate | done |
| 4 | Dashboard shell + design system | `feat/dashboard-shell` | delegate | done |
| 5 | Pipeline + export + bundle | `feat/pipeline-export` | coordinator | done |
| 6 | Dashboard: Overview, Samples | `feat/dash-overview-samples` | delegate | done |
| 7 | Dashboard: Response analysis | `feat/dash-response` | delegate | done |
| 8 | Dashboard: Baseline, Methods | `feat/dash-baseline-methods` | delegate | todo |
| 9 | Hardening + submission | `feat/hardening`, `docs/readme` | coordinator | todo |

## Phase 1

### WS-1 Foundation

Everything the parallel workstreams need to exist first. One PR.

**Owns:** `immune_atlas/__init__.py`, `immune_atlas/config.py`,
`immune_atlas/observability.py`, `pyproject.toml`, `requirements*.txt`,
`Makefile` (finalise), `.github/workflows/ci.yml` (finalise),
`contracts/dashboard-bundle.schema.json`, `tests/conftest.py`,
`tests/unit/test_config.py`, `tests/unit/test_observability.py`,
`.devcontainer/`.

**Deliverables**

- `config.py` with the constants in ARCHITECTURE §Configuration, a frozen
  `CohortFilter` dataclass, and path resolution with env overrides.
- `observability.py`: `configure_logging`, `get_logger`, `Timer`, `Metrics`
  with `to_dict()` / `write(path)`.
- `contracts/dashboard-bundle.schema.json`: complete JSON Schema (draft 2020-12)
  for the bundle in ARCHITECTURE, with `additionalProperties: false` throughout
  and a `schema_version` const. Include `contracts/fixtures/bundle.small.json`,
  a hand-sized valid instance used by dashboard tests.
- `tests/conftest.py`: fixtures for a temp repo copy, synthetic long/wide
  frames, and the real CSV path.
- CI workflow: remove the bootstrap guards on the `python` job (the package now
  exists) so lint and tests always run. The `pipeline`, `dashboard`, and `e2e`
  jobs keep their guards until WS-5 and WS-4 respectively remove them.
- Makefile targets all resolve; `make check` green.

**Acceptance**

- `python -c "import immune_atlas.config as c; print(c.POPULATIONS)"` works after
  `make setup`.
- `jsonschema` validates the fixture bundle against the contract.
- CI green on the PR; branch protection configured with the three required
  checks (done by `scripts/bootstrap_repo.sh`).

## Phase 2 (parallel)

### WS-2 Data layer

**Owns:** `immune_atlas/db/` (all files), `load_data.py`,
`tests/unit/test_schema.py`, `tests/unit/test_validate.py`,
`tests/unit/test_loader.py`, `tests/unit/test_queries.py`,
`tests/integration/test_load_data_script.py`.

**Must not change:** `config.py` constants, the schema DDL in ARCHITECTURE
(implement it verbatim in `schema.sql`; propose changes via PR comment first).

**Deliverables**

- `schema.sql` exactly as specified, plus `PRAGMA` settings in `connection.py`
  (`foreign_keys = ON`, `journal_mode = OFF` during bulk load for speed and
  byte-stability, then back).
- `validate.py`: implements DATA_NOTES §Invariants, collects all problems,
  raises `DataContractError` with them.
- `loader.py`: `init_db(db_path)`, `load_csv(conn, csv_path) -> LoadReport`,
  `run(csv_path, db_path) -> LoadReport`. Fresh database each run. Populations
  inserted from `config.POPULATIONS` with display names and sort order.
- `queries.py`: functions listed in ARCHITECTURE §Queries, returning DataFrames
  with documented column sets. Part 4 aggregations must be SQL, not pandas.
- `load_data.py`: ≤ 30 lines; resolves paths from config; calls `run`; prints a
  one-line summary; exits non-zero on failure. Must work with no arguments and
  before `pip install -e .` (it is run from the repo root, so the package is
  importable).

**Tests**

- Schema: every table and view exists; check constraints reject bad rows; FK
  enforcement rejects orphans; unique constraint on (subject, type, time).
- Validator: one test per invariant with a minimal failing CSV, plus a test that
  multiple problems are reported together.
- Loader: small synthetic CSV round-trips; running twice yields identical row
  counts and identical file bytes; real CSV loads 10,500 samples / 3,500 subjects
  / 52,500 counts.
- Queries: `v_cell_frequencies` columns and ordering; cohort query returns
  1,968 rows; baseline breakdown returns the DATA_NOTES numbers; form answer
  10206.15.
- Script: `subprocess.run([sys.executable, "load_data.py"])` in a temp copy of
  the repo creates `cell_counts.db`; running it again succeeds.

**Acceptance:** all of the above green; `python load_data.py` completes in under
5 seconds on the real file.

### WS-3 Analysis

**Owns:** `immune_atlas/analysis/` (all files), `tests/unit/test_frequencies.py`,
`tests/unit/test_response.py`, `tests/unit/test_subsets.py`,
`tests/unit/test_plots.py`.

**Must not change:** `config.py`; the result column names listed below (they
are also field names in the bundle schema).

**Deliverables**

- `frequencies.py`: `compute_frequencies(long)`, `to_wide(freqs)`. Output
  columns exactly `config.FREQUENCY_COLUMNS`.
- `response.py`: `compare_response(freqs, unit="sample"|"subject") ->
  ResponseComparison` (a dataclass holding a DataFrame with columns
  `population, n_yes, n_no, mean_yes, mean_no, sd_yes, sd_no, median_yes,
  median_no, iqr_low_yes, iqr_high_yes, iqr_low_no, iqr_high_no, u_statistic,
  p_value, q_value, effect_size, welch_p, significant_raw, significant_adjusted`,
  plus `unit`, `n_samples`, `n_subjects`, `alpha`). `compare_response_by_time`.
  `distributions(freqs)` returning per-population, per-group value lists for the
  bundle. Method details per ADR-0002 in docstrings.
- `subsets.py`: `summarise_baseline(samples_df) -> BaselineSummary` with the
  three breakdowns, asserting the sample/subject distinction explicitly.
- `plots.py`: `response_boxplots(freqs, out_dir) -> list[Path]`; Agg backend;
  colours from a `PALETTE` constant that mirrors `dashboard/src/lib/palette.ts`
  (values listed in DASHBOARD_UX §Colour). Deterministic output: fixed figure
  size, DPI, `metadata={"Software": None}` so PNG bytes are stable, jitter from a
  seeded RNG.

**Tests**

- Frequencies: hand-computed 2-sample example; percentages sum to 100; column
  names and order; error on a sample with total 0.
- Response: synthetic cohort with a planted shift in one population yields that
  population as `significant_adjusted` and the others not; null case yields no
  significant populations; effect-size sign convention; BH monotonicity;
  degenerate group (< 3 values) produces nulls plus a warning rather than an
  exception; per-subject aggregation collapses three rows to one.
- Subsets: counts by project use samples, by response/sex use distinct subjects
  (test with a subject that has two baseline samples to prove the distinction).
- Plots: files produced for each population and the combined figure; running
  twice gives identical bytes.

**Acceptance:** all green; every public function has a docstring stating input
columns and output columns.

### WS-4 Dashboard shell + design system

**Owns:** `dashboard/` (everything), `.github/workflows/ci.yml` dashboard job
(edit only that job).

**Must not change:** the bundle contract. Develop against
`contracts/fixtures/bundle.small.json` copied to `public/data/bundle.json` by
`npm run dev:fixture`.

**Deliverables**

- `create-next-app` with TypeScript, App Router, Tailwind, ESLint, `src/` dir;
  `output: "export"`; `npm run gen:types` (json-schema-to-typescript) producing
  `src/lib/bundle.types.ts`, committed.
- `lib/bundle.ts` (fetch `/data/bundle.json`, validate `schema_version`,
  expose `useBundle()` with loading and error states), `lib/filters.ts`,
  `lib/stats-format.ts`, `lib/palette.ts`.
- Layout and navigation for the five routes; design tokens (colour, type,
  spacing) as CSS variables from DASHBOARD_UX §Visual direction; the cohort
  definition strip component; the empty/loading/error states.
- Chart primitives on Visx: `BoxPlot` (with jittered points and hover),
  `DistributionBars`, `SmallMultiples` wrapper; each with a `<DataTable>`
  fallback toggle for accessibility.
- Vitest + Testing Library configured with coverage; Playwright configured with
  one smoke test (home renders) so WS-6–8 add to it.

**Tests:** `lib/` fully unit-tested; component tests for the cohort strip and the
box plot (renders n per group, respects reduced motion); `npm run build` succeeds
with the fixture bundle.

**Acceptance:** `make dashboard` (with the fixture) serves a navigable shell on
port 3000; Lighthouse accessibility ≥ 95 on the shell; visual review against
DASHBOARD_UX's "avoid" list recorded in the PR.

## Phase 3

### WS-5 Pipeline + export + bundle

**Owns:** `immune_atlas/export.py`, `immune_atlas/pipeline.py`, `outputs/`,
`dashboard/public/data/bundle.json`, `tests/unit/test_export.py`,
`tests/integration/test_pipeline.py`, `tests/integration/test_determinism.py`,
CI `pipeline` job (remove the WS-1 skip).

**Deliverables**

- `export.py`: writers for each output in ARCHITECTURE §Outputs, with the
  formatting rules; `build_bundle(...)` assembling the bundle from analysis
  results and metrics, validated against the contract before writing.
- `pipeline.py`: stage list, `PipelineContext`, `main()` CLI with `--only`,
  metrics for every stage, run report.
- `outputs/response_comparison.md`: a short human-readable report (cohort,
  method, table, one-paragraph conclusion, sensitivity and time-stratified notes).
- Generated outputs committed; `make pipeline` on a clean checkout produces no
  diff in data files (plots and the database are checked structurally, see
  ADR-0004).

**Tests:** export formatting (float formats, sort order, no timestamps); bundle
validates; full pipeline in a temp dir produces every expected file and the
DATA_NOTES numbers; determinism (two runs, byte-equal except `pipeline_run.json`).

**Acceptance:** CI `pipeline` job green including the `git diff --exit-code`
step and the `make dashboard` curl.

## Phase 4 (parallel)

Each WS owns its route directory under `dashboard/src/app/`, its components
under `dashboard/src/components/<route>/`, and its tests. Shared components in
`components/charts|tables|filters|layout` are owned by WS-4's author; changes
there go through a separate small PR.

### WS-6 Dashboard: Overview and Samples

- `/`: what the dataset is (counts of projects, subjects, samples, populations,
  time points), the study structure at a glance (conditions × treatments ×
  sample types), and direct entry points to the three questions.
- `/samples`: the Part 2 table — every sample, population, count, percentage —
  with a global filter bar (project, condition, treatment, sample type, time,
  response, sex), sortable columns, per-sample composition bars, CSV download
  of the filtered view, and a "sum to 100" indicator per sample.

### WS-7 Dashboard: Response analysis

- `/response`: cohort strip (melanoma → miraclib → PBMC → 1,968 samples /
  656 subjects), five box plots as small multiples with jittered samples,
  statistics table with p, q, effect size, medians, n; toggle per-sample /
  per-subject; time-point facet (all / 0 / 7 / 14); plain-language finding block
  generated from the numbers (never hard-coded); method footnote linking to
  `/methods`; PNG/CSV export.

### WS-8 Dashboard: Baseline cohort and Methods

- `/baseline`: the Part 4 cohort — filter definition, n samples / n subjects,
  the three breakdowns as compact bar charts with exact numbers, the sample list
  with subject metadata, CSV download. Include the form-question figure as a
  labelled aside with its own filter definition so it is not confused with the
  Part 4 cohort.
- `/methods`: schema diagram, test descriptions from ADR-0002, data provenance
  from the run report (input checksum, row counts, stage timings, library
  versions), links to the repository files.

**Tests for WS-6–8:** unit tests for every derived-data function; component tests
for filters and tables; one Playwright test per route that asserts the key
number(s) from DATA_NOTES appear on screen.

## Phase 5

### WS-9 Hardening and submission

- Playwright suite complete and in CI; flakiness budget zero (retries = 0).
- `README.md` written to SPEC §R.3: quickstart for Codespaces, schema with
  rationale and scaling, code structure and why, findings summary with the
  caveats from ADR-0002, dashboard link, how to run tests.
- Vercel project connected to `main`; production URL in README; a preview
  deployment per PR.
- Fresh Codespace run of `make setup && make pipeline && make dashboard`
  recorded in the PR.
- Final pass of the SPEC checklist; every row ticked with evidence.
- `docs/PLAN.md` status table all `done`; worktrees removed; branches deleted.

## Working agreements for this plan

- One PR per workstream unless a WS section says otherwise. Shared-component
  changes during Phase 4 go in their own small PRs to keep the route PRs clean.
- A workstream that discovers a needed interface change stops and raises it;
  the coordinator updates ARCHITECTURE / contracts in a dedicated PR, then the
  dependent workstreams rebase.
- Status changes in this file happen in the PR that causes them.
