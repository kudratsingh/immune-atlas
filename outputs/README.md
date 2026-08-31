# Generated outputs

Everything in this directory is produced by `make pipeline` and committed so the
results can be read without running anything. Regenerating on the same input
yields identical files; CI checks this.

| File | Produced by | Contents |
| ---- | ----------- | -------- |
| `cell_frequencies.csv` | Part 2 | `sample, total_count, population, count, percentage` — one row per sample × population |
| `response_comparison.csv` | Part 3 | Per-population statistics, responders vs non-responders (per-sample, per-subject, per-time-point rows tagged by `unit` / `time`) |
| `response_comparison.md` | Part 3 | Human-readable report with method and conclusion |
| `plots/response_boxplot_<population>.png` | Part 3 | One box plot per population |
| `plots/response_boxplots.png` | Part 3 | All five populations in one figure |
| `baseline_subset.csv` | Part 4 | The baseline melanoma miraclib PBMC samples with subject metadata |
| `baseline_subset_summary.json` | Part 4 | Counts by project, response, and sex |
| `form_answer.json` | — | The form question, its filter, n, and the mean B-cell count |
| `pipeline_run.json` | — | Run report: input checksum, stage timings, row counts, warnings, versions |

The dashboard reads none of these directly; it reads
`dashboard/public/data/bundle.json`, which the same pipeline run writes.
