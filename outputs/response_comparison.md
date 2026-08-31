# Responders vs non-responders — melanoma, miraclib, PBMC

Cohort: melanoma subjects treated with miraclib, PBMC samples at all time points — 1,968 samples from 656 subjects (responders 331 subjects / 993 samples; non-responders 325 / 975).

Method: two-sided Mann-Whitney U test on per-sample relative frequencies, rank-biserial correlation as the effect size (positive = responders higher), Benjamini-Hochberg adjustment across the 5 populations at alpha = 0.05, with Welch's t-test as a secondary check (ADR-0002).

| Population | Median % (R) | Median % (NR) | p | q | Effect size r | q < 0.05 |
| --- | ---: | ---: | ---: | ---: | ---: | :-- |
| B cells | 9.43 | 9.79 | 0.0557 | 0.139 | -0.050 | no |
| CD8 T cells | 24.73 | 24.60 | 0.639 | 0.639 | -0.012 | no |
| CD4 T cells | 30.22 | 29.66 | 0.0133 | 0.0667 | +0.064 | no |
| NK cells | 14.51 | 14.80 | 0.121 | 0.202 | -0.040 | no |
| Monocytes | 19.61 | 19.94 | 0.163 | 0.204 | -0.036 | no |

## Conclusion

No population remains significant after Benjamini-Hochberg adjustment across the 5 populations. CD4 T cells reaches unadjusted p = 0.0133 with a higher responder median (30.22% vs 29.66%) but does not clear the adjusted threshold (q = 0.0667), so it is reported as suggestive rather than significant.

## Sensitivity analysis (per subject)

Each subject contributes several samples while response is a subject-level label, so the per-sample test overstates independence. Averaging each subject's percentages to one value per subject (n = 656 subjects) removes that pseudo-replication. The per-subject test gives CD4 T cells p = 0.0124 (q = 0.0621) — consistent with the per-sample analysis.

## Time-stratified view

- Day 0: no population below p < 0.05.
- Day 7: CD4 T cells p = 0.0297.
- Day 14: B cells p = 0.0144.

Separation appears only after treatment starts, so these markers read as response indicators rather than baseline predictors.

Provenance: `data/cell-count.csv` (sha256 `011373475d37417d`), 1,968 cohort samples from 656 subjects.
