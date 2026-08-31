from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from immune_atlas import pipeline
from immune_atlas.analysis.subsets import BaselineSummary
from immune_atlas.observability import Metrics


def _context(tmp_path: Path) -> pipeline.PipelineContext:
    return pipeline.PipelineContext(
        csv_path=tmp_path / "cell-count.csv",
        db_path=tmp_path / "cell_counts.db",
        outputs_dir=tmp_path / "outputs",
        plots_dir=tmp_path / "outputs" / "plots",
        bundle_path=tmp_path / "bundle.json",
        contract_path=tmp_path / "contract.json",
        metrics=Metrics(source_sha256="0" * 64),
    )


def test_run_pipeline_rejects_an_unknown_stage_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown stage: nope"):
        pipeline.run_pipeline(_context(tmp_path), only="nope")


def test_stages_wrap_failures_in_a_named_stage_error(tmp_path: Path) -> None:
    context = _context(tmp_path)
    with pytest.raises(pipeline.StageError, match="stage cell_frequencies failed") as excinfo:
        pipeline.run_pipeline(context, only="cell_frequencies")
    assert excinfo.value.stage == "cell_frequencies"
    assert isinstance(excinfo.value.__cause__, FileNotFoundError)
    assert "make pipeline" in str(excinfo.value.__cause__)


def test_from_config_requires_the_input_csv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(pipeline.config, "CSV_PATH", tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError, match="input CSV not found"):
        pipeline.PipelineContext.from_config()


def test_main_reports_a_missing_csv_and_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(pipeline.config, "CSV_PATH", tmp_path / "missing.csv")
    assert pipeline.main([]) == 1
    assert "pipeline failed" in capsys.readouterr().err


def test_main_reports_a_failing_stage_and_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = tmp_path / "cell-count.csv"
    csv_path.write_text("not,a,real,file\n")
    monkeypatch.setattr(pipeline.config, "CSV_PATH", csv_path)
    monkeypatch.setattr(pipeline.config, "DB_PATH", tmp_path / "cell_counts.db")
    monkeypatch.setattr(pipeline.config, "OUTPUTS_DIR", tmp_path / "outputs")
    monkeypatch.setattr(pipeline.config, "PLOTS_DIR", tmp_path / "outputs" / "plots")
    assert pipeline.main([]) == 1
    assert "stage load_database failed" in capsys.readouterr().err


def test_main_rejects_an_unknown_only_argument() -> None:
    with pytest.raises(SystemExit):
        pipeline.main(["--only", "nope"])


def test_verify_baseline_raises_when_sql_and_pandas_disagree() -> None:
    summary = BaselineSummary(
        n_samples=2,
        n_subjects=2,
        by_project=pd.DataFrame({"project": ["prj1"], "n_samples": [2]}),
        by_response=pd.DataFrame({"response": ["yes"], "n_subjects": [2]}),
        by_sex=pd.DataFrame({"sex": ["M"], "n_subjects": [2]}),
        sample_ids=("s0", "s1"),
    )
    breakdown = pipeline.queries.BaselineBreakdown(
        by_project=pd.DataFrame({"project": ["prj1"], "n_samples": [2]}),
        by_response=pd.DataFrame({"response": ["yes"], "n_subjects": [1]}),
        by_sex=pd.DataFrame({"sex": ["M"], "n_subjects": [2]}),
    )
    with pytest.raises(RuntimeError, match="baseline breakdown by response disagrees"):
        pipeline._verify_baseline(summary, breakdown)


def test_verify_baseline_accepts_matching_breakdowns_in_any_order() -> None:
    summary = BaselineSummary(
        n_samples=2,
        n_subjects=2,
        by_project=pd.DataFrame({"project": ["prj1"], "n_samples": [2]}),
        by_response=pd.DataFrame({"response": ["no", "yes"], "n_subjects": [1, 1]}),
        by_sex=pd.DataFrame({"sex": ["F", "M"], "n_subjects": [1, 1]}),
        sample_ids=("s0", "s1"),
    )
    breakdown = pipeline.queries.BaselineBreakdown(
        by_project=pd.DataFrame({"project": ["prj1"], "n_samples": [2]}),
        by_response=pd.DataFrame({"response": ["yes", "no"], "n_subjects": [1, 1]}),
        by_sex=pd.DataFrame({"sex": ["M", "F"], "n_subjects": [1, 1]}),
    )
    pipeline._verify_baseline(summary, breakdown)
