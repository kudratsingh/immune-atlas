# Dataset notes

Profile of `data/cell-count.csv` as received. The numbers here are reference
values for integration tests and for sanity-checking pipeline output. If the input
file ever changes, regenerate this document from the pipeline metrics rather than
editing it by hand.

Input checksum (SHA-256, first 16 hex): `011373475d37417d`.

## Shape

- 10,500 rows, 15 columns, no missing values except `response`.
- One row per sample; `sample` is unique.
- 3,500 subjects; every subject has exactly three samples at
  `time_from_treatment_start` ∈ {0, 7, 14}.
- 3 projects: prj1 (1,500 subjects), prj2 (1,000), prj3 (1,000). Subject IDs are
  unique across projects.

## Columns

| Column | Type | Values | Level |
| ------ | ---- | ------ | ----- |
| project | text | prj1, prj2, prj3 | subject |
| subject | text | sbj0000 … | subject |
| condition | text | melanoma, carcinoma, healthy | subject |
| age | integer | | subject |
| sex | text | M, F | subject |
| treatment | text | miraclib, phauximab, none | subject |
| response | text or null | yes, no, null | subject |
| sample | text | sample00000 … | sample |
| sample_type | text | PBMC, WB | sample |
| time_from_treatment_start | integer | 0, 7, 14 | sample |
| b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte | integer | counts | sample × population |

"Level" records the granularity at which the value varies. Every subject-level
column is constant across a subject's three samples in this file. The loader
enforces this as a data contract (see ADR-0001); a violation is an error, not
something to average away.

## Invariants the loader enforces

1. Required columns present with the expected types.
2. `sample` unique.
3. All five counts are non-negative integers; total per sample > 0.
4. `sex` ∈ {M, F}; `response` ∈ {yes, no, null}; `time_from_treatment_start` ≥ 0.
5. `project, condition, age, sex, treatment, response` constant per subject.
6. `response` is null exactly when the subject is untreated (`treatment = none`).
   In this file that coincides with `condition = healthy` (1,422 rows).

## Reference numbers

Used by `tests/integration/`.

**Part 3 cohort** (melanoma, miraclib, PBMC): 1,968 samples from 656 subjects.
Responders: 331 subjects / 993 samples. Non-responders: 325 subjects / 975 samples.

Per-sample Mann–Whitney U on relative frequency, responders vs non-responders:

| Population | Median % yes | Median % no | p (two-sided) | BH q |
| ---------- | ------------ | ----------- | ------------- | ---- |
| b_cell | 9.43 | 9.79 | 0.056 | 0.139 |
| cd8_t_cell | 24.73 | 24.60 | 0.639 | 0.639 |
| cd4_t_cell | 30.22 | 29.66 | 0.013 | 0.067 |
| nk_cell | 14.51 | 14.80 | 0.121 | 0.202 |
| monocyte | 19.61 | 19.94 | 0.163 | 0.204 |

Per-subject sensitivity analysis (mean percentage over a subject's three samples)
gives cd4_t_cell p ≈ 0.012 and nothing else below 0.10.

Stratified by time point, the separation appears after treatment starts, not at
baseline: cd4_t_cell differs at day 7 (p ≈ 0.03) and b_cell at day 14 (p ≈ 0.014),
while no population differs at day 0. This matters for the "predict response"
framing and should be stated plainly in the report and the dashboard.

**Part 4 baseline cohort** (melanoma, miraclib, PBMC, time 0): 656 samples, one per
subject.

- By project: prj1 = 384, prj3 = 272 (prj2 has no melanoma miraclib PBMC samples).
- By response (subjects): yes = 331, no = 325.
- By sex (subjects): M = 344, F = 312.

**Form question** (melanoma, male, responder, time 0, all sample types and
treatments): 485 samples, mean `b_cell` = **10206.15**.

## Distribution notes

- Total cells per sample: min 84,247; mean ≈ 100,345; max 122,788. Relative
  frequencies are therefore well-behaved percentages with no near-zero totals.
- Count distributions are right-skewed with a handful of high outliers per
  population; a rank-based test is the safer default (ADR-0002).
