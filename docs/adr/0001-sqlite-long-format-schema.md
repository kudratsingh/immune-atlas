# 0001. Normalised SQLite schema with long-format counts

Status: Accepted
Date: 2026-08-30

## Context

The input is one CSV row per sample with subject metadata repeated on every row
and five cell populations as columns. The assignment asks for a schema that models
the data "effectively" and for a written explanation of how it would scale to
hundreds of projects, thousands of samples, and new kinds of analytics.

Profiling the file (DATA_NOTES) shows four entities hiding in it: projects,
subjects (condition, age, sex, treatment, response are constant per subject),
samples (type, time point), and per-sample population counts.

## Decision

Five tables — `projects`, `subjects`, `samples`, `cell_populations`,
`cell_counts` — with counts stored long (one row per sample × population) and a
`cell_populations` lookup carrying display names and sort order. Constraints
encode the data contract: check constraints on sex/response/counts, a unique key
on `(subject, sample_type, time)`, foreign keys on. Two views (`v_sample_totals`,
`v_cell_frequencies`) express Part 2 in SQL.

The loader validates that subject-level columns are constant per subject and
fails if they are not, rather than silently picking one value.

## Alternatives considered

- **Single wide table mirroring the CSV.** Fastest to write; fails the scaling
  question. Adding a sixth population is an `ALTER TABLE`, every analysis has to
  enumerate columns, and subject metadata is duplicated per sample with no
  guarantee of consistency.
- **Long table for counts but no subject table.** Removes the duplication of
  counts but keeps repeating subject metadata on every sample; response and
  treatment are subject facts and should live once.
- **Fully generic EAV store for all metadata.** Maximally flexible, hostile to
  query, and unnecessary when the metadata columns are known and typed.
- **Separate treatment-course table.** Would allow a subject to change treatment
  mid-study. Not supported by the data (treatment is constant per subject) and
  would complicate every cohort query; noted as the first migration to make if
  the study design changes.

## Consequences

- Scaling: thousands of samples × dozens of populations is a few hundred thousand
  narrow rows — trivial for SQLite, and the same DDL runs on Postgres. New
  analytics (per-population trends, ratios between populations, panel comparisons)
  are `GROUP BY` queries, not schema changes. Hundreds of projects are rows in
  `projects` and a foreign key; per-project partitioning or row-level security is
  a deployment concern on Postgres, not a schema change.
- The Part 2 table is a view, so it can never drift from the counts.
- Some queries need one more join than a flat table; the indexes in
  `schema.sql` cover the cohort and population access paths used here.
- `sample_type` and `condition` are free text with validation in Python rather
  than lookup tables. Promoting them to lookup tables is straightforward and would
  be done once controlled vocabularies exist.
