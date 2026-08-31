from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from immune_atlas import config, export
from immune_atlas.observability import Metrics
from immune_atlas.pipeline import STAGES, PipelineContext, run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_OUTPUTS = (
    "cell_frequencies.csv",
    "response_comparison.csv",
    "response_comparison.md",
    "baseline_subset.csv",
    "baseline_subset_summary.json",
    "form_answer.json",
    "pipeline_run.json",
)
EXPECTED_PLOTS = (
    *(f"response_boxplot_{population}.png" for population in config.POPULATIONS),
    "response_boxplots.png",
)

REFERENCE_P_VALUES = {
    "b_cell": 0.056,
    "cd8_t_cell": 0.639,
    "cd4_t_cell": 0.013,
    "nk_cell": 0.121,
    "monocyte": 0.163,
}
REFERENCE_Q_VALUES = {
    "b_cell": 0.139,
    "cd8_t_cell": 0.639,
    "cd4_t_cell": 0.067,
    "nk_cell": 0.202,
    "monocyte": 0.204,
}


def _run_context(base: Path) -> PipelineContext:
    csv_path = REPO_ROOT / "data" / "cell-count.csv"
    return PipelineContext(
        csv_path=csv_path,
        db_path=base / "cell_counts.db",
        outputs_dir=base / "outputs",
        plots_dir=base / "outputs" / "plots",
        bundle_path=base / "bundle.json",
        contract_path=REPO_ROOT / "contracts" / "dashboard-bundle.schema.json",
        metrics=Metrics(source_sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest()),
    )


@pytest.fixture(scope="module")
def pipeline_run(tmp_path_factory: pytest.TempPathFactory) -> PipelineContext:
    context = _run_context(tmp_path_factory.mktemp("pipeline"))
    run_pipeline(context)
    context.close()
    return context


@pytest.mark.integration
def test_pipeline_produces_every_expected_file(pipeline_run: PipelineContext) -> None:
    for name in EXPECTED_OUTPUTS:
        assert (pipeline_run.outputs_dir / name).is_file(), name
    for name in EXPECTED_PLOTS:
        assert (pipeline_run.plots_dir / name).is_file(), name
    assert pipeline_run.bundle_path.is_file()
    assert pipeline_run.db_path.is_file()


@pytest.mark.integration
def test_part2_table_covers_every_sample_and_population(pipeline_run: PipelineContext) -> None:
    lines = (pipeline_run.outputs_dir / "cell_frequencies.csv").read_text().splitlines()
    assert lines[0] == ",".join(config.FREQUENCY_COLUMNS)
    assert len(lines) == 52_500 + 1


@pytest.mark.integration
def test_baseline_summary_matches_the_reference_numbers(pipeline_run: PipelineContext) -> None:
    payload = json.loads((pipeline_run.outputs_dir / "baseline_subset_summary.json").read_text())
    assert payload["n_samples"] == 656
    assert payload["n_subjects"] == 656
    assert payload["by_project"] == [
        {"project": "prj1", "n_samples": 384},
        {"project": "prj3", "n_samples": 272},
    ]
    assert payload["by_response"] == [
        {"response": "yes", "n_subjects": 331},
        {"response": "no", "n_subjects": 325},
    ]
    assert payload["by_sex"] == [
        {"sex": "M", "n_subjects": 344},
        {"sex": "F", "n_subjects": 312},
    ]


@pytest.mark.integration
def test_form_answer_matches_the_reference_number(pipeline_run: PipelineContext) -> None:
    payload = json.loads((pipeline_run.outputs_dir / "form_answer.json").read_text())
    assert payload["mean_b_cell"] == 10206.15
    assert payload["n_samples"] == 485
    assert payload["n_subjects"] == 485


@pytest.mark.integration
def test_bundle_validates_and_carries_the_reference_statistics(
    pipeline_run: PipelineContext,
) -> None:
    bundle = json.loads(pipeline_run.bundle_path.read_text())
    export.validate_bundle(bundle, pipeline_run.contract_path)
    meta = bundle["meta"]
    assert (meta["n_rows"], meta["n_samples"], meta["n_subjects"]) == (10_500, 10_500, 3_500)
    assert bundle["response_analysis"]["n"] == {
        "samples_yes": 993,
        "samples_no": 975,
        "subjects_yes": 331,
        "subjects_no": 325,
    }
    by_population = {
        row["population"]: row for row in bundle["response_analysis"]["by_sample"]["rows"]
    }
    for population, expected_p in REFERENCE_P_VALUES.items():
        assert round(by_population[population]["p_value"], 3) == expected_p, population
        expected_q = REFERENCE_Q_VALUES[population]
        assert round(by_population[population]["q_value"], 3) == expected_q, population
    assert not any(row["significant_adjusted"] for row in by_population.values())
    by_subject = {
        row["population"]: row for row in bundle["response_analysis"]["by_subject"]["rows"]
    }
    assert round(by_subject["cd4_t_cell"]["p_value"], 3) == 0.012


@pytest.mark.integration
def test_time_stratified_separation_appears_only_after_baseline(
    pipeline_run: PipelineContext,
) -> None:
    bundle = json.loads(pipeline_run.bundle_path.read_text())
    by_time = {
        item["time"]: {
            row["population"] for row in item["comparison"]["rows"] if row["significant_raw"]
        }
        for item in bundle["response_analysis"]["by_time"]
    }
    assert by_time[0] == set()
    assert by_time[7] == {"cd4_t_cell"}
    assert by_time[14] == {"b_cell"}


@pytest.mark.integration
def test_bundle_run_section_is_deterministic_while_the_report_keeps_timings(
    pipeline_run: PipelineContext,
) -> None:
    bundle = json.loads(pipeline_run.bundle_path.read_text())
    assert all(stage["seconds"] == 0.0 for stage in bundle["run"]["stages"])
    report = json.loads((pipeline_run.outputs_dir / "pipeline_run.json").read_text())
    assert [stage["name"] for stage in report["stages"]] == [name for name, _ in STAGES[:-1]]
    assert any(stage["seconds"] > 0.0 for stage in report["stages"])
    assert report["warnings"] == []
    assert report["source_sha256"].startswith("011373475d37417d")


@pytest.mark.integration
def test_only_flag_runs_a_single_stage(tmp_path: Path) -> None:
    context = _run_context(tmp_path)
    run_pipeline(context, only="load_database")
    context.close()
    assert context.db_path.is_file()
    assert not context.outputs_dir.exists()


@pytest.mark.integration
def test_cli_module_runs_a_stage_in_a_repository_copy(temp_repo: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "immune_atlas.pipeline", "--only", "load_database"],
        cwd=temp_repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Pipeline complete: 1 stage" in result.stdout
    assert (temp_repo / "cell_counts.db").is_file()
