"""Write deterministic analysis outputs and the validated dashboard data bundle."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, cast

import jsonschema
import pandas as pd

from immune_atlas import config
from immune_atlas.analysis.response import ResponseComparison, TimeComparison
from immune_atlas.analysis.subsets import BaselineSummary
from immune_atlas.observability import Metrics, get_logger

_LOGGER = get_logger(__name__)

# The bundle is byte-diffed by CI (ADR-0004), so it carries a fixed generation
# timestamp; wall-clock provenance lives only in outputs/pipeline_run.json.
GENERATED_AT: Final = "2026-08-30T00:00:00Z"
SOURCE_FILE: Final = "data/cell-count.csv"
METHOD: Final = "Mann-Whitney U"
ADJUSTMENT: Final = "Benjamini-Hochberg"
FORM_QUESTION: Final = (
    "Considering melanoma males of all sample and treatment types, what is the "
    "average number of B cells for responders at time=0?"
)

_PERCENT_DECIMALS: Final = 6
_STAT_DIGITS: Final = 8
_DESCRIPTIVE_COLUMNS: Final = (
    "mean_yes",
    "mean_no",
    "sd_yes",
    "sd_no",
    "median_yes",
    "median_no",
    "iqr_low_yes",
    "iqr_high_yes",
    "iqr_low_no",
    "iqr_high_no",
    "effect_size",
)
_P_VALUE_COLUMNS: Final = ("p_value", "q_value", "welch_p")
_FLAG_COLUMNS: Final = ("significant_raw", "significant_adjusted")
_BASELINE_CSV_COLUMNS: Final = (
    "project",
    "subject",
    "condition",
    "age",
    "sex",
    "treatment",
    "response",
    "sample",
    "sample_type",
    "time_from_treatment_start",
)


def _stat(value: float | None) -> float | None:
    """Return a float trimmed to a fixed number of significant digits, or None."""
    if value is None or pd.isna(value):
        return None
    return float(f"{float(value):.{_STAT_DIGITS}g}")


def _percentage(value: float) -> float:
    """Round a percentage to the fixed decimal precision used in every output."""
    return round(float(value), _PERCENT_DECIMALS)


def _display(population: str) -> str:
    return config.POPULATION_DISPLAY_NAMES[population]


def _write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(payload: Mapping[str, object], path: Path) -> None:
    """Write a JSON object with sorted keys, two-space indentation, and a newline."""
    _write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", path)


def write_frequencies_csv(frequencies: pd.DataFrame, path: Path) -> None:
    """Write the Part 2 summary table with fixed column order and %.6f percentages."""
    frame = frequencies.loc[:, list(config.FREQUENCY_COLUMNS)].copy()
    frame["total_count"] = frame["total_count"].astype(int)
    frame["count"] = frame["count"].astype(int)
    frame["percentage"] = [f"{value:.6f}" for value in frame["percentage"].astype(float)]
    _write_text(frame.to_csv(index=False, lineterminator="\n"), path)


def _format_cell(value: float | None, spec: str) -> str:
    if value is None or pd.isna(value):
        return ""
    return format(float(value), spec)


def write_response_csv(comparison: ResponseComparison, path: Path) -> None:
    """Write the primary comparison table with %.6f descriptives and %.4g p-values."""
    frame = comparison.table.loc[:, list(config.RESPONSE_COMPARISON_COLUMNS)].copy()
    for column in ("n_yes", "n_no"):
        frame[column] = frame[column].astype(int)
    frame["u_statistic"] = [_format_cell(value, ".1f") for value in frame["u_statistic"]]
    for column in _DESCRIPTIVE_COLUMNS:
        frame[column] = [_format_cell(value, ".6f") for value in frame[column]]
    for column in _P_VALUE_COLUMNS:
        frame[column] = [_format_cell(value, ".4g") for value in frame[column]]
    for column in _FLAG_COLUMNS:
        frame[column] = ["true" if bool(value) else "false" for value in frame[column]]
    _write_text(frame.to_csv(index=False, lineterminator="\n"), path)


def write_baseline_csv(baseline_samples: pd.DataFrame, path: Path) -> None:
    """Write the Part 4 sample list with subject metadata, ordered by sample id."""
    frame = baseline_samples.loc[:, list(_BASELINE_CSV_COLUMNS)].copy()
    frame = frame.sort_values("sample", kind="stable")
    frame["age"] = frame["age"].astype(int)
    frame["time_from_treatment_start"] = frame["time_from_treatment_start"].astype(int)
    _write_text(frame.to_csv(index=False, lineterminator="\n"), path)


def _project_records(by_project: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {"project": str(record["project"]), "n_samples": int(record["n_samples"])}
        for record in by_project.to_dict("records")
    ]


def _response_records(by_response: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {"response": str(record["response"]), "n_subjects": int(record["n_subjects"])}
        for record in by_response.to_dict("records")
    ]


def _sex_records(by_sex: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {"sex": str(record["sex"]), "n_subjects": int(record["n_subjects"])}
        for record in by_sex.to_dict("records")
    ]


def _baseline_payload(
    summary: BaselineSummary,
    *,
    by_project: pd.DataFrame,
    by_response: pd.DataFrame,
    by_sex: pd.DataFrame,
) -> dict[str, object]:
    return {
        "filter": config.BASELINE_COHORT.to_dict(),
        "n_samples": summary.n_samples,
        "n_subjects": summary.n_subjects,
        "by_project": _project_records(by_project),
        "by_response": _response_records(by_response),
        "by_sex": _sex_records(by_sex),
    }


def write_baseline_summary_json(
    summary: BaselineSummary,
    *,
    by_project: pd.DataFrame,
    by_response: pd.DataFrame,
    by_sex: pd.DataFrame,
    path: Path,
) -> None:
    """Write the Part 4 breakdowns from the SQL aggregations with the cohort filter."""
    write_json(
        _baseline_payload(summary, by_project=by_project, by_response=by_response, by_sex=by_sex),
        path,
    )


def build_form_answer(*, mean_b_cell: float, n_samples: int, n_subjects: int) -> dict[str, object]:
    """Return the form-question payload shared by form_answer.json and the bundle."""
    return {
        "question": FORM_QUESTION,
        "filter": dict(config.FORM_FILTER),
        "n_samples": n_samples,
        "n_subjects": n_subjects,
        "mean_b_cell": mean_b_cell,
    }


def _interval(low: float | None, high: float | None) -> list[float] | None:
    low_value = _stat(low)
    high_value = _stat(high)
    if low_value is None or high_value is None:
        return None
    return [low_value, high_value]


def _comparison_rows(table: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in table.to_dict("records"):
        rows.append(
            {
                "population": str(record["population"]),
                "n_yes": int(record["n_yes"]),
                "n_no": int(record["n_no"]),
                "mean_yes": _stat(record["mean_yes"]),
                "mean_no": _stat(record["mean_no"]),
                "sd_yes": _stat(record["sd_yes"]),
                "sd_no": _stat(record["sd_no"]),
                "median_yes": _stat(record["median_yes"]),
                "median_no": _stat(record["median_no"]),
                "iqr_yes": _interval(record["iqr_low_yes"], record["iqr_high_yes"]),
                "iqr_no": _interval(record["iqr_low_no"], record["iqr_high_no"]),
                "u_statistic": _stat(record["u_statistic"]),
                "p_value": _stat(record["p_value"]),
                "q_value": _stat(record["q_value"]),
                "effect_size": _stat(record["effect_size"]),
                "welch_p": _stat(record["welch_p"]),
                "significant_raw": bool(record["significant_raw"]),
                "significant_adjusted": bool(record["significant_adjusted"]),
            }
        )
    return rows


def comparison_payload(comparison: ResponseComparison) -> dict[str, object]:
    """Return the bundle representation of one response comparison."""
    return {
        "unit": comparison.unit,
        "alpha": comparison.alpha,
        "method": METHOD,
        "adjustment": ADJUSTMENT,
        "n_samples": comparison.n_samples,
        "n_subjects": comparison.n_subjects,
        "rows": _comparison_rows(comparison.table),
    }


def _population_info() -> list[dict[str, object]]:
    return [
        {"name": name, "display_name": _display(name), "sort_order": index}
        for index, name in enumerate(config.POPULATIONS)
    ]


def _meta(samples: pd.DataFrame, source_sha256: str) -> dict[str, object]:
    return {
        "generated_at": GENERATED_AT,
        "source_file": SOURCE_FILE,
        "source_sha256": source_sha256,
        "n_rows": len(samples),
        "n_samples": int(samples["sample"].nunique()),
        "n_subjects": int(samples["subject"].nunique()),
        "n_projects": int(samples["project"].nunique()),
        "populations": _population_info(),
        "time_points": sorted(int(v) for v in samples["time_from_treatment_start"].unique()),
        "conditions": sorted(str(v) for v in samples["condition"].unique()),
        "treatments": sorted(str(v) for v in samples["treatment"].unique()),
        "sample_types": sorted(str(v) for v in samples["sample_type"].unique()),
    }


def _sample_records(samples: pd.DataFrame, frequencies: pd.DataFrame) -> list[dict[str, object]]:
    counts = frequencies.pivot(index="sample", columns="population", values="count")
    percentages = frequencies.pivot(index="sample", columns="population", values="percentage")
    counts_map = counts.to_dict("index")
    percentages_map = percentages.to_dict("index")
    records: list[dict[str, object]] = []
    for record in samples.sort_values("sample", kind="stable").to_dict("records"):
        sample_id = str(record["sample"])
        records.append(
            {
                "sample": sample_id,
                "subject": str(record["subject"]),
                "project": str(record["project"]),
                "condition": str(record["condition"]),
                "age": int(record["age"]),
                "sex": str(record["sex"]),
                "treatment": str(record["treatment"]),
                "response": None if pd.isna(record["response"]) else str(record["response"]),
                "sample_type": str(record["sample_type"]),
                "time": int(record["time_from_treatment_start"]),
                "total_count": int(record["total_count"]),
                "counts": {name: int(counts_map[sample_id][name]) for name in config.POPULATIONS},
                "percentages": {
                    name: _percentage(percentages_map[sample_id][name])
                    for name in config.POPULATIONS
                },
            }
        )
    return records


def _frequency_records(frequencies: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {
            "sample": str(record["sample"]),
            "total_count": int(record["total_count"]),
            "population": str(record["population"]),
            "count": int(record["count"]),
            "percentage": _percentage(record["percentage"]),
        }
        for record in frequencies.to_dict("records")
    ]


def _distribution_records(
    distribution_groups: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    for group in distribution_groups:
        points = [
            {
                "sample": str(point["sample"]),
                "subject": str(point["subject"]),
                "time": int(cast(int, point["time"])),
                "percentage": _percentage(float(cast(float, point["percentage"]))),
            }
            for point in cast(Sequence[Mapping[str, object]], group["points"])
        ]
        groups.append(
            {"population": group["population"], "response": group["response"], "points": points}
        )
    return groups


def group_counts(cohort: pd.DataFrame) -> dict[str, int]:
    """Count samples and subjects per response group in a cohort frequency frame."""
    per_sample = cohort.drop_duplicates("sample")
    per_subject = cohort.drop_duplicates("subject")
    return {
        "samples_yes": int((per_sample["response"] == "yes").sum()),
        "samples_no": int((per_sample["response"] == "no").sum()),
        "subjects_yes": int((per_subject["response"] == "yes").sum()),
        "subjects_no": int((per_subject["response"] == "no").sum()),
    }


def _run_payload(metrics: Metrics) -> dict[str, object]:
    # Stage seconds are wall-clock and the interpreter's micro version varies by
    # environment; both would change the bundle's bytes between runs, so the
    # bundle zeroes the former and truncates the latter to major.minor.
    # pipeline_run.json keeps the real values.
    payload = metrics.to_dict()
    stages = cast(Sequence[Mapping[str, object]], payload["stages"])
    payload["stages"] = [{**stage, "seconds": 0.0} for stage in stages]
    payload["python_version"] = ".".join(metrics.python_version.split(".")[:2])
    return payload


def build_bundle(
    *,
    samples: pd.DataFrame,
    frequencies: pd.DataFrame,
    cohort: pd.DataFrame,
    by_sample: ResponseComparison,
    by_subject: ResponseComparison,
    by_time: Sequence[TimeComparison],
    distribution_groups: Sequence[Mapping[str, object]],
    baseline: BaselineSummary,
    baseline_by_project: pd.DataFrame,
    baseline_by_response: pd.DataFrame,
    baseline_by_sex: pd.DataFrame,
    form_answer: Mapping[str, object],
    metrics: Metrics,
) -> dict[str, object]:
    """Assemble the dashboard bundle from query frames and analysis results.

    `samples` carries one metadata row per sample; `frequencies` and `cohort` are the
    long frequency frames from the data layer; the remaining inputs are the analysis
    results and the SQL baseline breakdowns. The output is byte-stable across runs:
    a fixed `generated_at`, zeroed stage seconds, and fixed float precision.
    """
    baseline_payload = _baseline_payload(
        baseline,
        by_project=baseline_by_project,
        by_response=baseline_by_response,
        by_sex=baseline_by_sex,
    )
    baseline_payload["sample_ids"] = list(baseline.sample_ids)
    return {
        "schema_version": config.SCHEMA_VERSION,
        "meta": _meta(samples, metrics.source_sha256),
        "samples": _sample_records(samples, frequencies),
        "frequencies_long": _frequency_records(frequencies),
        "response_analysis": {
            "cohort": config.RESPONSE_COHORT.to_dict(),
            "n": group_counts(cohort),
            "by_sample": comparison_payload(by_sample),
            "by_subject": comparison_payload(by_subject),
            "by_time": [
                {"time": item.time, "comparison": comparison_payload(item.comparison)}
                for item in by_time
            ],
            "distributions": _distribution_records(distribution_groups),
        },
        "baseline_subset": baseline_payload,
        "form_answer": dict(form_answer),
        "run": _run_payload(metrics),
    }


def validate_bundle(bundle: Mapping[str, object], contract_path: Path) -> None:
    """Validate the bundle against the JSON Schema contract, raising on violations."""
    schema = json.loads(contract_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=bundle, schema=schema)


def write_bundle(bundle: Mapping[str, object], *, contract_path: Path, path: Path) -> None:
    """Validate the bundle against the contract, then write it as deterministic JSON.

    Unlike the files under outputs/, the bundle is a network payload, so it is
    written compact rather than indented; keys stay sorted for stable bytes.
    """
    validate_bundle(bundle, contract_path)
    _write_text(
        f"{json.dumps(bundle, sort_keys=True, separators=(',', ':'))}\n",
        path,
    )
    _LOGGER.info("bundle_written path=%s bytes=%d", path, path.stat().st_size)


def _fmt_p(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.3g}"


def _fmt_median(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.2f}"


def _conclusion(by_sample: ResponseComparison) -> str:
    records = by_sample.table.to_dict("records")
    adjusted = [record for record in records if record["significant_adjusted"]]
    raw_only = [
        record
        for record in records
        if record["significant_raw"] and not record["significant_adjusted"]
    ]
    sentences: list[str] = []
    if not adjusted:
        sentences.append(
            "No population remains significant after "
            f"{ADJUSTMENT} adjustment across the {len(records)} populations."
        )
    for record in adjusted:
        direction = "higher" if record["median_yes"] > record["median_no"] else "lower"
        sentences.append(
            f"{_display(str(record['population']))} differs between responders and "
            f"non-responders (p = {_fmt_p(record['p_value'])}, q = {_fmt_p(record['q_value'])}); "
            f"the median is {direction} in responders "
            f"({_fmt_median(record['median_yes'])}% vs {_fmt_median(record['median_no'])}%)."
        )
    for record in raw_only:
        direction = "higher" if record["median_yes"] > record["median_no"] else "lower"
        sentences.append(
            f"{_display(str(record['population']))} reaches unadjusted "
            f"p = {_fmt_p(record['p_value'])} with a {direction} responder median "
            f"({_fmt_median(record['median_yes'])}% vs {_fmt_median(record['median_no'])}%) "
            f"but does not clear the adjusted threshold (q = {_fmt_p(record['q_value'])}), "
            "so it is reported as suggestive rather than significant."
        )
    if not adjusted and not raw_only:
        sentences.append(
            f"No population separates the groups at unadjusted p < {by_sample.alpha} either."
        )
    return " ".join(sentences)


def _sensitivity(by_sample: ResponseComparison, by_subject: ResponseComparison) -> str:
    records = by_subject.table.to_dict("records")
    hits = [record for record in records if record["significant_raw"]]
    sample_hits = {
        str(record["population"])
        for record in by_sample.table.to_dict("records")
        if record["significant_raw"]
    }
    text = (
        "Each subject contributes several samples while response is a subject-level "
        "label, so the per-sample test overstates independence. Averaging each "
        f"subject's percentages to one value per subject (n = {by_subject.n_subjects:,} "
        "subjects) removes that pseudo-replication."
    )
    if hits:
        listing = ", ".join(
            f"{_display(str(record['population']))} p = {_fmt_p(record['p_value'])} "
            f"(q = {_fmt_p(record['q_value'])})"
            for record in hits
        )
        agreement = (
            "consistent with the per-sample analysis"
            if {str(record["population"]) for record in hits} == sample_hits
            else "which differs from the per-sample analysis"
        )
        return f"{text} The per-subject test gives {listing} — {agreement}."
    return f"{text} No population reaches p < {by_subject.alpha} on the per-subject test."


def _time_lines(by_time: Sequence[TimeComparison]) -> list[str]:
    lines: list[str] = []
    baseline_clear = False
    later_hits = False
    for item in by_time:
        hits = [
            record
            for record in item.comparison.table.to_dict("records")
            if record["significant_raw"]
        ]
        if hits:
            listing = "; ".join(
                f"{_display(str(record['population']))} p = {_fmt_p(record['p_value'])}"
                for record in hits
            )
            lines.append(f"- Day {item.time}: {listing}.")
            if item.time > 0:
                later_hits = True
        else:
            lines.append(f"- Day {item.time}: no population below p < {item.comparison.alpha}.")
            if item.time == 0:
                baseline_clear = True
    if baseline_clear and later_hits:
        lines.extend(
            [
                "",
                "Separation appears only after treatment starts, so these markers read "
                "as response indicators rather than baseline predictors.",
            ]
        )
    return lines


def write_report_md(
    *,
    by_sample: ResponseComparison,
    by_subject: ResponseComparison,
    by_time: Sequence[TimeComparison],
    group_counts: Mapping[str, int],
    source_sha256: str,
    path: Path,
) -> None:
    """Write the human-readable response report; every number comes from the inputs."""
    cohort = config.RESPONSE_COHORT
    lines = [
        f"# Responders vs non-responders — {cohort.condition}, {cohort.treatment}, "
        f"{cohort.sample_type}",
        "",
        f"Cohort: {cohort.condition} subjects treated with {cohort.treatment}, "
        f"{cohort.sample_type} samples at all time points — {by_sample.n_samples:,} samples "
        f"from {by_sample.n_subjects:,} subjects (responders "
        f"{group_counts['subjects_yes']:,} subjects / {group_counts['samples_yes']:,} samples; "
        f"non-responders {group_counts['subjects_no']:,} / {group_counts['samples_no']:,}).",
        "",
        f"Method: two-sided {METHOD} test on per-sample relative frequencies, "
        "rank-biserial correlation as the effect size (positive = responders higher), "
        f"{ADJUSTMENT} adjustment across the {len(config.POPULATIONS)} populations at "
        f"alpha = {by_sample.alpha}, with Welch's t-test as a secondary check (ADR-0002).",
        "",
        "| Population | Median % (R) | Median % (NR) | p | q | Effect size r | q < 0.05 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | :-- |",
    ]
    for record in by_sample.table.to_dict("records"):
        effect = record["effect_size"]
        effect_text = "n/a" if effect is None or pd.isna(effect) else f"{float(effect):+.3f}"
        lines.append(
            f"| {_display(str(record['population']))} "
            f"| {_fmt_median(record['median_yes'])} "
            f"| {_fmt_median(record['median_no'])} "
            f"| {_fmt_p(record['p_value'])} "
            f"| {_fmt_p(record['q_value'])} "
            f"| {effect_text} "
            f"| {'yes' if record['significant_adjusted'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            _conclusion(by_sample),
            "",
            "## Sensitivity analysis (per subject)",
            "",
            _sensitivity(by_sample, by_subject),
            "",
            "## Time-stratified view",
            "",
            *_time_lines(by_time),
            "",
            f"Provenance: `{SOURCE_FILE}` (sha256 `{source_sha256[:16]}`), "
            f"{by_sample.n_samples:,} cohort samples from {by_sample.n_subjects:,} subjects.",
            "",
        ]
    )
    _write_text("\n".join(lines), path)
