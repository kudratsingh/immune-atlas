# 0002. Statistical method for the responder comparison

Status: Accepted
Date: 2026-08-30

## Context

Part 3 asks which cell populations differ in relative frequency between
responders and non-responders among melanoma patients on miraclib (PBMC only),
with statistics that would convince a sceptical colleague. Constraints from the
data: five populations tested; relative frequencies are bounded and right-skewed
with outliers; each subject contributes three samples (days 0, 7, 14), and
response is a subject-level label, so samples are not independent observations.

## Decision

Primary analysis, per population, on per-sample percentages as the assignment
specifies ("using the data reported in the summary table"):

- Two-sided **Mann–Whitney U** test. Rank-based, no normality assumption, robust
  to the outliers present in the counts.
- **Rank-biserial correlation** as the effect size, reported with medians and
  IQRs per group so the magnitude is visible alongside the p-value.
- **Benjamini–Hochberg** adjustment across the five populations; a population is
  reported as significant at q < 0.05 and, separately, at unadjusted p < 0.05 so
  the reader sees exactly which bar it clears.
- Welch's t-test reported as a secondary column, because that is the test most
  readers will ask about.

Two required companions to the primary analysis:

- **Per-subject sensitivity analysis**: average each subject's percentages across
  its time points, then run the same test on one value per subject. This removes
  the pseudo-replication and is the more defensible unit of analysis for a
  subject-level outcome.
- **Time-stratified view**: the same per-sample test within each time point,
  because a marker that separates groups only after treatment starts is a
  response indicator, not a baseline predictor. The dataset shows exactly this
  pattern (DATA_NOTES).

## Alternatives considered

- **t-test only.** Simpler, but the count distributions have heavy right tails
  and the assignment explicitly wants statistics that withstand scrutiny.
- **Mixed-effects model with subject random intercept.** The correct model for
  repeated measures, and the natural next step. Rejected for the primary analysis
  because it changes the question from "do frequencies differ" to a model-based
  estimate that is harder to present in a boxplot-driven report, and because the
  per-subject aggregation already addresses independence for a 656-subject cohort.
  Noted as follow-up work.
- **Bonferroni.** More conservative than needed with five correlated tests; BH is
  the standard for this kind of screen.
- **No multiple-comparison correction.** Would report cd4_t_cell as significant at
  p = 0.013 and stop. That is the finding most likely to be challenged, so the
  adjusted value is shown next to it rather than hidden.

## Consequences

- The report says, for this dataset: cd4_t_cell differs at unadjusted p ≈ 0.013
  (q ≈ 0.067, not significant after BH); no other population reaches p < 0.05
  pooled; stratified by time, cd4_t_cell separates at day 7 and b_cell at day 14
  while nothing separates at baseline. That is a nuanced conclusion, and the
  dashboard is designed to make it readable rather than to hide it.
- Statistics live in `analysis/response.py` as pure functions with the test
  choice, effect-size convention, and adjustment method in docstrings.
