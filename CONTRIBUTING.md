# Contributing

Short version of the working agreements. `CLAUDE.md` has the same rules with the
detail an automated collaborator needs.

## Branches and pull requests

- `main` is protected; all changes arrive by pull request with green CI.
- Branch from an up-to-date `main`: `feat/<area>-<description>`, `fix/…`,
  `docs/…`, `chore/…`, `test/…`.
- One concern per PR. Aim for under 500 changed lines; split otherwise.
- Squash merge only. The PR title is the commit subject on `main`, written as a
  Conventional Commit (`feat(analysis): compare responders by population`).
- Enable auto-merge when the PR is ready: `gh pr merge --auto --squash`. It merges
  when the required checks pass and the branch is current with `main`.

## Commits

- Conventional Commits, imperative mood, subject ≤ 72 characters.
- Body explains why when the diff does not make it obvious. No trailers.
- Regenerate and commit outputs (`make pipeline`) in the same PR as the code that
  changed them; CI fails on a stale output.

## Before opening a PR

```
make check          # ruff, mypy, eslint, tsc, pytest with coverage, vitest
```

## Code style

- Python: ruff (format + lint), mypy strict on the package, Google-style
  docstrings, module docstring on every file, comments only where the why is not
  obvious.
- TypeScript: strict, ESLint, Prettier. Generated types come from
  `contracts/`; do not edit them by hand.
- Tests accompany every change in behaviour.

## Documentation

- Decisions that change the architecture get an ADR in `docs/adr/`.
- `docs/PLAN.md` status is updated in the PR that changes it.
