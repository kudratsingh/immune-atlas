from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pandas as pd
import pytest

from immune_atlas import config, export
from immune_atlas.analysis.response import (
    compare_response,
    compare_response_by_time,
    distributions,
)
from immune_atlas.analysis.subsets import summarise_baseline
from immune_atlas.observability import Metrics

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "dashboard-bundle.schema.json"


def _synthetic_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (samples_meta, freq_long) with a planted cd4 shift for responders."""
    meta_rows: list[dict[str, object]] = []
    freq_rows: list[dict[str, object]] = []
    for i in range(8):
        response = "yes" if i % 2 == 0 else "no"
        shift = 80 if response == "yes" else 0
        for t in (0, 7):
            sample = f"s{t:02d}{i}"
            counts = {
                "b_cell": 100 + i,
                "cd8_t_cell": 200 + 2 * i,
                "cd4_t_cell": 300 + shift + i,
                "nk_cell": 150 + i,
                "monocyte": 250 - shift + i,
            }
            total = sum(counts.values())
            meta_rows.append(
                {
                    "sample": sample,
                    "subject": f"sbj{i}",
                    "project": "prj1" if i < 5 else "prj2",
                    "condition": "melanoma",
                    "age": 40 + i,
                    "sex": "M" if i % 3 == 0 else "F",
                    "treatment": "miraclib",
                    "response": response,
                    "sample_type": "PBMC",
                    "time_from_treatment_start": t,
                    "total_count": total,
                }
            )
            for population, count in counts.items():
                freq_rows.append(
                    {
                        "sample": sample,
                        "total_count": total,
                        "population": population,
                        "count": count,
                        "percentage": 100.0 * count / total,
                    }
                )
    return pd.DataFrame(meta_rows), pd.DataFrame(freq_rows)


@pytest.fixture(scope="module")
def dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    return _synthetic_dataset()


@pytest.fixture(scope="module")
def cohort(dataset: tuple[pd.DataFrame, pd.DataFrame]) -> pd.DataFrame:
    samples, freqs = dataset
    return freqs.merge(
        samples.loc[:, ["sample", "subject", "response", "time_from_treatment_start"]],
        on="sample",
    )


def test_write_frequencies_csv_uses_fixed_columns_and_float_format(
    dataset: tuple[pd.DataFrame, pd.DataFrame], tmp_path: Path
) -> None:
    _, freqs = dataset
    path = tmp_path / "cell_frequencies.csv"
    export.write_frequencies_csv(freqs, path)
    lines = path.read_text().splitlines()
    assert lines[0] == ",".join(config.FREQUENCY_COLUMNS)
    assert len(lines) == len(freqs) + 1
    first = lines[1].split(",")
    assert first[2] == "b_cell"
    assert "." in first[4]
    assert len(first[4].split(".")[1]) == 6
    assert path.read_text().endswith("\n")


def test_write_frequencies_csv_is_byte_deterministic(
    dataset: tuple[pd.DataFrame, pd.DataFrame], tmp_path: Path
) -> None:
    _, freqs = dataset
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    export.write_frequencies_csv(freqs, first)
    export.write_frequencies_csv(freqs, second)
    assert first.read_bytes() == second.read_bytes()


def test_write_response_csv_formats_statistics_and_flags(
    cohort: pd.DataFrame, tmp_path: Path
) -> None:
    comparison = compare_response(cohort, unit="sample")
    path = tmp_path / "response_comparison.csv"
    export.write_response_csv(comparison, path)
    lines = path.read_text().splitlines()
    assert lines[0] == ",".join(config.RESPONSE_COMPARISON_COLUMNS)
    frame = pd.read_csv(path, dtype=str)
    cd4 = frame.loc[frame["population"] == "cd4_t_cell"].iloc[0]
    assert cd4["significant_adjusted"] == "true"
    assert float(cd4["p_value"]) < 0.05
    assert len(cd4["median_yes"].split(".")[1]) == 6
    b_cell = frame.loc[frame["population"] == "b_cell"].iloc[0]
    assert b_cell["significant_adjusted"] == "false"


def test_write_response_csv_leaves_degenerate_statistics_empty(tmp_path: Path) -> None:
    small = pd.DataFrame(
        {
            "sample": [f"s{i}" for i in range(2)] * 5,
            "subject": [f"b{i}" for i in range(2)] * 5,
            "response": ["yes", "no"] * 5,
            "population": [p for p in config.POPULATIONS for _ in range(2)],
            "percentage": [20.0] * 10,
        }
    )
    with pytest.warns(RuntimeWarning):
        comparison = compare_response(small, unit="sample")
    path = tmp_path / "degenerate.csv"
    export.write_response_csv(comparison, path)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    row = frame.iloc[0]
    assert row["p_value"] == ""
    assert row["mean_yes"] == ""
    assert row["significant_raw"] == "false"


def test_write_json_sorts_keys_and_ends_with_newline(tmp_path: Path) -> None:
    path = tmp_path / "payload.json"
    export.write_json({"zulu": 1, "alpha": {"b": 2, "a": 1}}, path)
    text = path.read_text()
    assert text.startswith('{\n  "alpha"')
    assert text.index('"alpha"') < text.index('"zulu"')
    assert text.endswith("}\n")


def test_write_baseline_csv_orders_rows_by_sample(
    dataset: tuple[pd.DataFrame, pd.DataFrame], tmp_path: Path
) -> None:
    samples, _ = dataset
    baseline = samples.loc[samples["time_from_treatment_start"] == 0]
    shuffled = baseline.sort_values("subject", ascending=False)
    path = tmp_path / "baseline_subset.csv"
    export.write_baseline_csv(shuffled, path)
    frame = pd.read_csv(path)
    assert list(frame.columns) == list(export._BASELINE_CSV_COLUMNS)
    assert frame["sample"].is_monotonic_increasing
    assert len(frame) == len(baseline)


def test_baseline_summary_json_reports_sql_breakdowns_and_filter(
    dataset: tuple[pd.DataFrame, pd.DataFrame], tmp_path: Path
) -> None:
    samples, _ = dataset
    baseline = samples.loc[samples["time_from_treatment_start"] == 0]
    summary = summarise_baseline(baseline)
    by_project = pd.DataFrame({"project": ["prj1", "prj2"], "n_samples": [5, 3]})
    by_response = pd.DataFrame({"response": ["yes", "no"], "n_subjects": [4, 4]})
    by_sex = pd.DataFrame({"sex": ["M", "F"], "n_subjects": [3, 5]})
    path = tmp_path / "baseline_subset_summary.json"
    export.write_baseline_summary_json(
        summary, by_project=by_project, by_response=by_response, by_sex=by_sex, path=path
    )
    payload = json.loads(path.read_text())
    assert payload["filter"] == config.BASELINE_COHORT.to_dict()
    assert payload["n_samples"] == 8
    assert payload["by_response"][0] == {"response": "yes", "n_subjects": 4}
    assert "sample_ids" not in payload


def test_build_form_answer_uses_configured_filter() -> None:
    payload = export.build_form_answer(mean_b_cell=10206.15, n_samples=485, n_subjects=485)
    assert payload["filter"] == dict(config.FORM_FILTER)
    assert payload["question"] == export.FORM_QUESTION
    assert payload["mean_b_cell"] == 10206.15


def _build_bundle(
    samples: pd.DataFrame, freqs: pd.DataFrame, cohort: pd.DataFrame
) -> dict[str, object]:
    baseline = samples.loc[samples["time_from_treatment_start"] == 0]
    summary = summarise_baseline(baseline)
    metrics = Metrics(source_sha256="0" * 64)
    metrics.record_stage("load_database", seconds=1.25, rows_in=16, rows_out=80)
    return export.build_bundle(
        samples=samples,
        frequencies=freqs,
        cohort=cohort,
        by_sample=compare_response(cohort, unit="sample"),
        by_subject=compare_response(cohort, unit="subject"),
        by_time=compare_response_by_time(cohort),
        distribution_groups=distributions(cohort),
        baseline=summary,
        baseline_by_project=summary.by_project,
        baseline_by_response=summary.by_response,
        baseline_by_sex=summary.by_sex,
        form_answer=export.build_form_answer(mean_b_cell=1.5, n_samples=4, n_subjects=4),
        metrics=metrics,
    )


def test_build_bundle_validates_against_the_contract(
    dataset: tuple[pd.DataFrame, pd.DataFrame], cohort: pd.DataFrame
) -> None:
    samples, freqs = dataset
    bundle = _build_bundle(samples, freqs, cohort)
    export.validate_bundle(bundle, CONTRACT_PATH)
    meta = bundle["meta"]
    assert isinstance(meta, dict)
    assert meta["generated_at"] == export.GENERATED_AT
    assert meta["n_samples"] == 16
    assert meta["time_points"] == [0, 7]


def test_build_bundle_zeroes_stage_seconds_for_determinism(
    dataset: tuple[pd.DataFrame, pd.DataFrame], cohort: pd.DataFrame
) -> None:
    samples, freqs = dataset
    bundle = _build_bundle(samples, freqs, cohort)
    run = bundle["run"]
    assert isinstance(run, dict)
    assert [stage["seconds"] for stage in run["stages"]] == [0.0]
    assert run["stages"][0]["rows_out"] == 80
    assert run["python_version"].count(".") == 1


def test_build_bundle_serialization_is_deterministic(
    dataset: tuple[pd.DataFrame, pd.DataFrame], cohort: pd.DataFrame
) -> None:
    samples, freqs = dataset
    first = json.dumps(_build_bundle(samples, freqs, cohort), sort_keys=True)
    second = json.dumps(_build_bundle(samples, freqs, cohort), sort_keys=True)
    assert first == second


def test_write_bundle_rejects_a_contract_violation(
    dataset: tuple[pd.DataFrame, pd.DataFrame], cohort: pd.DataFrame, tmp_path: Path
) -> None:
    samples, freqs = dataset
    bundle = _build_bundle(samples, freqs, cohort)
    bundle["schema_version"] = "2.0"
    path = tmp_path / "bundle.json"
    with pytest.raises(jsonschema.ValidationError):
        export.write_bundle(bundle, contract_path=CONTRACT_PATH, path=path)
    assert not path.exists()


def test_write_bundle_writes_compact_newline_terminated_json(
    dataset: tuple[pd.DataFrame, pd.DataFrame], cohort: pd.DataFrame, tmp_path: Path
) -> None:
    samples, freqs = dataset
    bundle = _build_bundle(samples, freqs, cohort)
    path = tmp_path / "bundle.json"
    export.write_bundle(bundle, contract_path=CONTRACT_PATH, path=path)
    text = path.read_text()
    assert text.endswith("\n")
    assert "\n" not in text[:-1]
    assert json.loads(text)["schema_version"] == config.SCHEMA_VERSION


def test_report_md_states_the_planted_finding(cohort: pd.DataFrame, tmp_path: Path) -> None:
    by_sample = compare_response(cohort, unit="sample")
    path = tmp_path / "response_comparison.md"
    export.write_report_md(
        by_sample=by_sample,
        by_subject=compare_response(cohort, unit="subject"),
        by_time=compare_response_by_time(cohort),
        group_counts=export.group_counts(cohort),
        source_sha256="0" * 64,
        path=path,
    )
    text = path.read_text()
    assert "CD4 T cells differs between responders and non-responders" in text
    assert "## Sensitivity analysis (per subject)" in text
    assert "- Day 0:" in text
    assert "- Day 7:" in text
    assert "16 samples from 8 subjects" in text


def test_report_md_states_a_null_result_without_inventing_findings(tmp_path: Path) -> None:
    rows: list[dict[str, object]] = []
    for i in range(8):
        response = "yes" if i % 2 == 0 else "no"
        for population in config.POPULATIONS:
            rows.append(
                {
                    "sample": f"s{i}",
                    "subject": f"b{i}",
                    "response": response,
                    "population": population,
                    "percentage": 20.0 + (i % 4),
                    "time_from_treatment_start": 0,
                }
            )
    cohort = pd.DataFrame(rows)
    by_sample = compare_response(cohort, unit="sample")
    path = tmp_path / "null.md"
    export.write_report_md(
        by_sample=by_sample,
        by_subject=compare_response(cohort, unit="subject"),
        by_time=compare_response_by_time(cohort),
        group_counts=export.group_counts(cohort),
        source_sha256="0" * 64,
        path=path,
    )
    text = path.read_text()
    assert "No population remains significant" in text
    assert "suggestive" not in text
    assert "response indicators rather than baseline predictors" not in text
