# 0005. Testing and CI strategy

Status: Accepted
Date: 2026-08-30

## Context

The repository will be graded automatically and read by reviewers. Confidence has
to come from tests that run on every PR, and the branching model (feature
branches, auto-merge on green) only works if CI is the actual gate.

## Decision

Four layers:

1. **Unit tests** (pytest, Vitest) for every module, using small synthetic data
   with known answers. Statistics are tested with a planted effect and a null
   case; the loader with malformed CSVs.
2. **Integration tests** (pytest) that run the real entry points on the real CSV
   into a temporary directory and assert the reference numbers in DATA_NOTES,
   plus a determinism test that runs the pipeline twice and compares bytes.
3. **Pipeline job** in CI that executes exactly what the grader will: `make setup`,
   `make pipeline`, then `make dashboard` in the background with a curl against
   port 3000, and `git diff --exit-code` on generated files.
4. **End-to-end smoke tests** (Playwright) against the static build: each route
   renders, the main filter changes the sample table, the response page shows the
   statistics table.

Coverage gates: 90% for `immune_atlas/`, 80% for `dashboard/src`. Lint (ruff,
mypy, ESLint, tsc) runs before tests.

Branch protection on `main`: PR required, the `python`, `dashboard`, and
`pipeline` checks required, branches must be up to date, linear history, no
force pushes, admins included. Auto-merge is enabled at the repository level and
requested per PR; squash merge only.

## Alternatives considered

- **Coverage without integration tests.** Would pass while `load_data.py` fails
  from a fresh checkout. The subprocess test exists precisely because the entry
  point is a script.
- **Full Playwright coverage of every interaction.** Slow and brittle; the pure
  functions in `lib/` carry the logic and are unit-tested, so e2e stays at smoke
  level.
- **Required reviews on PRs.** Sensible for a team; a solo repository would block
  on itself. Zero required approvals, with CI as the gate.

## Consequences

- CI time is dominated by `npm ci` and the Playwright browser install; both are
  cached by lockfile hash.
- Because required checks must be up to date with `main`, parallel PRs need a
  branch update after each merge before their auto-merge fires. Documented in
  CLAUDE.md.
