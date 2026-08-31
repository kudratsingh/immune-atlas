"""Orchestrate the pipeline stages from database load to the dashboard bundle."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

import pandas as pd

from immune_atlas import config, export
from immune_atlas.analysis.plots import response_boxplots
from immune_atlas.analysis.response import (
    ResponseComparison,
    TimeComparison,
    compare_response,
    compare_response_by_time,
    distributions,
)
from immune_atlas.analysis.subsets import BaselineSummary, summarise_baseline
from immune_atlas.db import loader, queries
from immune_atlas.db.connection import connect
from immune_atlas.observability import Metrics, Timer, configure_logging, get_logger

_LOGGER = get_logger(__name__)


class StageError(RuntimeError):
    """Signal that one named pipeline stage failed."""

    def __init__(self, stage: str, error: BaseException) -> None:
        """Record the failing stage name alongside the original error."""
        super().__init__(f"stage {stage} failed: {error}")
        self.stage = stage


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(slots=True)
class PipelineContext:
    """Carry paths, the open database connection, metrics, and cached results."""

    csv_path: Path
    db_path: Path
    outputs_dir: Path
    plots_dir: Path
    bundle_path: Path
    contract_path: Path
    metrics: Metrics
    connection: sqlite3.Connection | None = None
    cache: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_config(cls) -> PipelineContext:
        """Build a context from the configured repository paths."""
        if not config.CSV_PATH.exists():
            raise FileNotFoundError(
                f"input CSV not found: {config.CSV_PATH}; the dataset belongs at "
                f"{export.SOURCE_FILE} in the repository root"
            )
        return cls(
            csv_path=config.CSV_PATH,
            db_path=config.DB_PATH,
            outputs_dir=config.OUTPUTS_DIR,
            plots_dir=config.PLOTS_DIR,
            bundle_path=config.DASHBOARD_BUNDLE_PATH,
            contract_path=config.CONTRACT_PATH,
            metrics=Metrics(source_sha256=_sha256(config.CSV_PATH)),
        )

    def require_connection(self) -> sqlite3.Connection:
        """Return the open connection, connecting to an existing database on demand."""
        if self.connection is None:
            if not self.db_path.exists():
                raise FileNotFoundError(
                    f"database not found: {self.db_path}; run `make pipeline` "
                    "(or the load_database stage) first"
                )
            self.connection = connect(self.db_path)
        return self.connection

    def close(self) -> None:
        """Close the database connection if one is open."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None


def _cohort(context: PipelineContext) -> pd.DataFrame:
    if "cohort" not in context.cache:
        cohort = config.RESPONSE_COHORT
        context.cache["cohort"] = queries.cohort_frequencies(
            context.require_connection(),
            condition=cohort.condition,
            treatment=cohort.treatment,
            sample_type=cohort.sample_type,
        )
    return cast(pd.DataFrame, context.cache["cohort"])


def _frequencies(context: PipelineContext) -> pd.DataFrame:
    if "frequencies" not in context.cache:
        context.cache["frequencies"] = queries.cell_frequencies(context.require_connection())
    return cast(pd.DataFrame, context.cache["frequencies"])


def _samples_meta(context: PipelineContext) -> pd.DataFrame:
    if "samples_meta" not in context.cache:
        context.cache["samples_meta"] = queries.sample_metadata(context.require_connection())
    return cast(pd.DataFrame, context.cache["samples_meta"])


def _record_warnings(context: PipelineContext, comparison: ResponseComparison) -> None:
    for message in comparison.warnings:
        context.metrics.add_warning(message)


def _by_sample(context: PipelineContext) -> ResponseComparison:
    if "by_sample" not in context.cache:
        comparison = compare_response(_cohort(context), unit="sample")
        _record_warnings(context, comparison)
        context.cache["by_sample"] = comparison
    return cast(ResponseComparison, context.cache["by_sample"])


def _by_subject(context: PipelineContext) -> ResponseComparison:
    if "by_subject" not in context.cache:
        comparison = compare_response(_cohort(context), unit="subject")
        _record_warnings(context, comparison)
        context.cache["by_subject"] = comparison
    return cast(ResponseComparison, context.cache["by_subject"])


def _by_time(context: PipelineContext) -> list[TimeComparison]:
    if "by_time" not in context.cache:
        items = compare_response_by_time(_cohort(context))
        for item in items:
            _record_warnings(context, item.comparison)
        context.cache["by_time"] = items
    return cast(list[TimeComparison], context.cache["by_time"])


def _distribution_groups(context: PipelineContext) -> list[dict[str, object]]:
    if "distribution_groups" not in context.cache:
        context.cache["distribution_groups"] = distributions(_cohort(context))
    return cast(list[dict[str, object]], context.cache["distribution_groups"])


def _baseline_frame(context: PipelineContext) -> pd.DataFrame:
    if "baseline_frame" not in context.cache:
        cohort = config.BASELINE_COHORT
        context.cache["baseline_frame"] = queries.baseline_samples(
            context.require_connection(),
            condition=cohort.condition,
            treatment=cohort.treatment,
            sample_type=cohort.sample_type,
            time=config.BASELINE_TIME,
        )
    return cast(pd.DataFrame, context.cache["baseline_frame"])


def _baseline_summary(context: PipelineContext) -> BaselineSummary:
    if "baseline_summary" not in context.cache:
        context.cache["baseline_summary"] = summarise_baseline(_baseline_frame(context))
    return cast(BaselineSummary, context.cache["baseline_summary"])


def _baseline_breakdown(context: PipelineContext) -> queries.BaselineBreakdown:
    if "baseline_breakdown" not in context.cache:
        cohort = config.BASELINE_COHORT
        context.cache["baseline_breakdown"] = queries.baseline_breakdown(
            context.require_connection(),
            condition=cohort.condition,
            treatment=cohort.treatment,
            sample_type=cohort.sample_type,
            time=config.BASELINE_TIME,
        )
    return cast(queries.BaselineBreakdown, context.cache["baseline_breakdown"])


def _sorted_records(frame: pd.DataFrame, key: str) -> list[dict[str, object]]:
    records = cast(
        list[dict[str, object]],
        frame.sort_values(key, kind="stable").to_dict("records"),
    )
    return [{k: v for k, v in record.items()} for record in records]


def _verify_baseline(summary: BaselineSummary, breakdown: queries.BaselineBreakdown) -> None:
    # The SQL and pandas aggregations count different things by design (samples
    # for project, subjects for response and sex); both paths must agree.
    pairs = (
        ("project", summary.by_project, breakdown.by_project),
        ("response", summary.by_response, breakdown.by_response),
        ("sex", summary.by_sex, breakdown.by_sex),
    )
    for key, pandas_frame, sql_frame in pairs:
        if _sorted_records(pandas_frame, key) != _sorted_records(sql_frame, key):
            raise RuntimeError(f"baseline breakdown by {key} disagrees between SQL and pandas")


def _form_payload(context: PipelineContext) -> dict[str, object]:
    if "form_payload" not in context.cache:
        meta = _samples_meta(context)
        subset = meta.loc[
            (meta["condition"] == config.FORM_FILTER["condition"])
            & (meta["sex"] == config.FORM_FILTER["sex"])
            & (meta["response"] == config.FORM_FILTER["response"])
            & (meta["time_from_treatment_start"] == config.FORM_FILTER["time"])
        ]
        context.cache["form_payload"] = export.build_form_answer(
            mean_b_cell=queries.form_answer(context.require_connection()),
            n_samples=int(subset["sample"].nunique()),
            n_subjects=int(subset["subject"].nunique()),
        )
    return cast(dict[str, object], context.cache["form_payload"])


def _stage_load_database(context: PipelineContext, timer: Timer) -> None:
    context.close()
    report = loader.run(context.csv_path, context.db_path)
    context.connection = connect(context.db_path)
    timer.rows_in = report.samples
    timer.set_rows_out(report.counts)


def _stage_cell_frequencies(context: PipelineContext, timer: Timer) -> None:
    frame = _frequencies(context)
    export.write_frequencies_csv(frame, context.outputs_dir / "cell_frequencies.csv")
    timer.set_rows_out(len(frame))


def _stage_response_comparison(context: PipelineContext, timer: Timer) -> None:
    timer.rows_in = len(_cohort(context))
    by_sample = _by_sample(context)
    export.write_response_csv(by_sample, context.outputs_dir / "response_comparison.csv")
    export.write_report_md(
        by_sample=by_sample,
        by_subject=_by_subject(context),
        by_time=_by_time(context),
        group_counts=export.group_counts(_cohort(context)),
        source_sha256=context.metrics.source_sha256,
        path=context.outputs_dir / "response_comparison.md",
    )
    timer.set_rows_out(len(by_sample.table))


def _stage_response_plots(context: PipelineContext, timer: Timer) -> None:
    cohort = _cohort(context)
    timer.rows_in = len(cohort)
    paths = response_boxplots(cohort, context.plots_dir)
    timer.set_rows_out(len(paths))


def _stage_baseline_subset(context: PipelineContext, timer: Timer) -> None:
    frame = _baseline_frame(context)
    timer.rows_in = len(frame)
    summary = _baseline_summary(context)
    breakdown = _baseline_breakdown(context)
    _verify_baseline(summary, breakdown)
    export.write_baseline_csv(frame, context.outputs_dir / "baseline_subset.csv")
    export.write_baseline_summary_json(
        summary,
        by_project=breakdown.by_project,
        by_response=breakdown.by_response,
        by_sex=breakdown.by_sex,
        path=context.outputs_dir / "baseline_subset_summary.json",
    )
    timer.set_rows_out(summary.n_samples)


def _stage_form_answer(context: PipelineContext, timer: Timer) -> None:
    payload = _form_payload(context)
    export.write_json(payload, context.outputs_dir / "form_answer.json")
    timer.set_rows_out(cast(int, payload["n_samples"]))


def _stage_dashboard_bundle(context: PipelineContext, timer: Timer) -> None:
    samples = _samples_meta(context)
    timer.rows_in = len(samples)
    breakdown = _baseline_breakdown(context)
    bundle = export.build_bundle(
        samples=samples,
        frequencies=_frequencies(context),
        cohort=_cohort(context),
        by_sample=_by_sample(context),
        by_subject=_by_subject(context),
        by_time=_by_time(context),
        distribution_groups=_distribution_groups(context),
        baseline=_baseline_summary(context),
        baseline_by_project=breakdown.by_project,
        baseline_by_response=breakdown.by_response,
        baseline_by_sex=breakdown.by_sex,
        form_answer=_form_payload(context),
        metrics=context.metrics,
    )
    export.write_bundle(bundle, contract_path=context.contract_path, path=context.bundle_path)
    timer.set_rows_out(len(samples))


def _stage_write_run_report(context: PipelineContext, timer: Timer) -> None:
    context.metrics.write(context.outputs_dir / "pipeline_run.json")
    timer.set_rows_out(len(context.metrics.stages))


StageFunction = Callable[[PipelineContext, Timer], None]
STAGES: Final[tuple[tuple[str, StageFunction], ...]] = (
    ("load_database", _stage_load_database),
    ("cell_frequencies", _stage_cell_frequencies),
    ("response_comparison", _stage_response_comparison),
    ("response_plots", _stage_response_plots),
    ("baseline_subset", _stage_baseline_subset),
    ("form_answer", _stage_form_answer),
    ("dashboard_bundle", _stage_dashboard_bundle),
    ("write_run_report", _stage_write_run_report),
)


def run_pipeline(context: PipelineContext, *, only: str | None = None) -> None:
    """Run every stage in order, or a single stage when `only` names one."""
    names = [name for name, _ in STAGES]
    if only is not None and only not in names:
        raise ValueError(f"unknown stage: {only}; expected one of {', '.join(names)}")
    for name, stage in STAGES:
        if only is not None and name != only:
            continue
        try:
            with Timer(name, context.metrics) as timer:
                stage(context, timer)
        except Exception as error:
            raise StageError(name, error) from error


def main(argv: Sequence[str] | None = None) -> int:
    """Run the pipeline CLI and return a process exit code."""
    configure_logging()
    parser = argparse.ArgumentParser(
        prog="python -m immune_atlas.pipeline",
        description="Generate every analysis output and the dashboard bundle.",
    )
    parser.add_argument(
        "--only",
        choices=[name for name, _ in STAGES],
        help="run a single stage (development only; assumes earlier stages ran)",
    )
    args = parser.parse_args(argv)
    try:
        context = PipelineContext.from_config()
    except Exception as error:
        print(f"pipeline failed: {error}", file=sys.stderr)
        return 1
    try:
        run_pipeline(context, only=cast(str | None, args.only))
    except StageError as error:
        print(f"pipeline failed: {error}", file=sys.stderr)
        return 1
    finally:
        context.close()
    stage_count = len(context.metrics.stages)
    print(
        f"Pipeline complete: {stage_count} stage{'s' if stage_count != 1 else ''}; "
        f"outputs in {context.outputs_dir} and {context.bundle_path}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
