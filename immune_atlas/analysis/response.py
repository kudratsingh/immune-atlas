"""Compare responder and non-responder relative-frequency distributions."""

from __future__ import annotations

import warnings as warning_module
from dataclasses import dataclass
from typing import Literal, cast

import numpy as np
import pandas as pd
from scipy import stats

from immune_atlas import config

AnalysisUnit = Literal["sample", "subject"]
_GROUPS = ("yes", "no")
_TIME_SOURCE_COLUMN = "time_from_treatment_start"


@dataclass(frozen=True, slots=True)
class ResponseComparison:
    """Hold one response comparison and its analysis-unit metadata.

    `table` columns are exactly `config.RESPONSE_COMPARISON_COLUMNS`; `unit` identifies
    whether its n values count samples or subjects. `n_samples` and `n_subjects`
    describe the complete filtered input cohort, and `warnings` lists populations
    whose groups were too small for statistics.
    """

    table: pd.DataFrame
    unit: AnalysisUnit
    n_samples: int
    n_subjects: int
    alpha: float
    warnings: tuple[str, ...] = ()

    @property
    def rows(self) -> pd.DataFrame:
        """Return the comparison rows with `config.RESPONSE_COMPARISON_COLUMNS`."""
        return self.table


@dataclass(frozen=True, slots=True)
class TimeComparison:
    """Pair an integer treatment-relative `time` with a sample-level comparison."""

    time: int
    comparison: ResponseComparison


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")


def _cohort_frame(frequencies: pd.DataFrame) -> pd.DataFrame:
    required = ("sample", "subject", "response", "population", "percentage")
    _require_columns(frequencies, required)
    cohort_columns = ("condition", "treatment", "sample_type")
    available = tuple(column for column in cohort_columns if column in frequencies.columns)
    if available and available != cohort_columns:
        raise ValueError("condition, treatment, and sample_type must be supplied together")
    frame = frequencies.copy()
    if available:
        cohort = config.RESPONSE_COHORT
        frame = frame.loc[
            (frame["condition"] == cohort.condition)
            & (frame["treatment"] == cohort.treatment)
            & (frame["sample_type"] == cohort.sample_type)
        ].copy()
    frame = frame.loc[frame["response"].isin(_GROUPS)].copy()
    if frame.empty:
        raise ValueError("response cohort contains no responder or non-responder rows")
    if frame.duplicated(["sample", "population"]).any():
        raise ValueError("each sample and population pair must occur exactly once")
    unknown = sorted(set(frame["population"].astype(str)) - set(config.POPULATIONS))
    if unknown:
        raise ValueError(f"unknown populations: {', '.join(unknown)}")
    percentages = pd.to_numeric(frame["percentage"], errors="coerce")
    if percentages.isna().any() or not np.isfinite(percentages.to_numpy(dtype=float)).all():
        raise ValueError("percentage values must be finite numbers")
    frame["percentage"] = percentages
    response_counts = frame.groupby("subject")["response"].nunique(dropna=False)
    if (response_counts != 1).any():
        raise ValueError("response must be constant within each subject")
    return frame


def _null_row(population: str, n_yes: int, n_no: int) -> dict[str, object]:
    row: dict[str, object] = {column: None for column in config.RESPONSE_COMPARISON_COLUMNS}
    row.update(
        {
            "population": population,
            "n_yes": n_yes,
            "n_no": n_no,
            "significant_raw": False,
            "significant_adjusted": False,
        }
    )
    return row


def _finite_or_none(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None


def _comparison_row(population: str, values: pd.DataFrame) -> tuple[dict[str, object], str | None]:
    yes = values.loc[values["response"] == "yes", "percentage"].to_numpy(dtype=float)
    no = values.loc[values["response"] == "no", "percentage"].to_numpy(dtype=float)
    n_yes, n_no = len(yes), len(no)
    if n_yes < 3 or n_no < 3:
        message = (
            f"{population}: statistics omitted because groups require at least 3 values "
            f"(yes={n_yes}, no={n_no})"
        )
        return _null_row(population, n_yes, n_no), message

    # U is defined for the non-responder group so ADR-0002's formula
    # 1 - 2U/(n_yes*n_no) is positive when responder values are higher.
    mann_whitney = stats.mannwhitneyu(no, yes, alternative="two-sided", method="auto")
    u_statistic = float(mann_whitney.statistic)
    with warning_module.catch_warnings():
        warning_module.simplefilter("ignore", RuntimeWarning)
        welch_p = float(stats.ttest_ind(yes, no, equal_var=False).pvalue)
    row: dict[str, object] = {
        "population": population,
        "n_yes": n_yes,
        "n_no": n_no,
        "mean_yes": float(np.mean(yes)),
        "mean_no": float(np.mean(no)),
        "sd_yes": float(np.std(yes, ddof=1)),
        "sd_no": float(np.std(no, ddof=1)),
        "median_yes": float(np.median(yes)),
        "median_no": float(np.median(no)),
        "iqr_low_yes": float(np.quantile(yes, 0.25)),
        "iqr_high_yes": float(np.quantile(yes, 0.75)),
        "iqr_low_no": float(np.quantile(no, 0.25)),
        "iqr_high_no": float(np.quantile(no, 0.75)),
        "u_statistic": u_statistic,
        "p_value": float(mann_whitney.pvalue),
        "q_value": None,
        "effect_size": 1.0 - (2.0 * u_statistic / (n_yes * n_no)),
        "welch_p": _finite_or_none(welch_p),
        "significant_raw": bool(mann_whitney.pvalue < config.ALPHA),
        "significant_adjusted": False,
    }
    return row, None


def compare_response(
    frequencies: pd.DataFrame,
    *,
    unit: AnalysisUnit = "sample",
    alpha: float = config.ALPHA,
) -> ResponseComparison:
    """Compare response groups with Mann-Whitney U, Welch, BH, and rank-biserial r.

    Input columns are `sample, subject, response, population, percentage`; optional
    `condition, treatment, sample_type` columns are jointly used to enforce the fixed
    response cohort. For `unit="subject"`, percentages are first averaged within
    `subject, response, population`. The output DataFrame columns are exactly
    `config.RESPONSE_COMPARISON_COLUMNS`. Tests are two-sided; BH adjusts valid p-values
    across configured populations. Rank-biserial `r = 1 - 2U/(n_yes*n_no)` uses U for
    non-responders, so positive values mean responders are higher. Groups below three
    values retain n, emit a warning, and have null descriptive and inferential values.
    """
    if unit not in ("sample", "subject"):
        raise ValueError("unit must be 'sample' or 'subject'")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be between 0 and 1")
    frame = _cohort_frame(frequencies)
    n_samples = int(frame["sample"].nunique())
    n_subjects = int(frame["subject"].nunique())
    analysis_frame: pd.DataFrame = frame
    if unit == "subject":
        analysis_frame = (
            frame.groupby(["subject", "response", "population"], sort=True)["percentage"]
            .mean()
            .rename("percentage")
            .reset_index()
        )

    rows: list[dict[str, object]] = []
    messages: list[str] = []
    for population in config.POPULATIONS:
        row, message = _comparison_row(
            population, analysis_frame.loc[analysis_frame["population"] == population]
        )
        if message is not None:
            warning_module.warn(message, RuntimeWarning, stacklevel=2)
            messages.append(message)
        rows.append(row)

    table = pd.DataFrame(rows, columns=config.RESPONSE_COMPARISON_COLUMNS)
    valid = table["p_value"].notna()
    if valid.any():
        p_values = table.loc[valid, "p_value"].to_numpy(dtype=float)
        adjusted = np.atleast_1d(stats.false_discovery_control(p_values, method="bh"))
        table.loc[valid, "q_value"] = adjusted
        table.loc[valid, "significant_raw"] = table.loc[valid, "p_value"] < alpha
        table.loc[valid, "significant_adjusted"] = table.loc[valid, "q_value"] < alpha
    table["significant_raw"] = table["significant_raw"].astype(bool)
    table["significant_adjusted"] = table["significant_adjusted"].astype(bool)
    return ResponseComparison(
        table=table,
        unit=unit,
        n_samples=n_samples,
        n_subjects=n_subjects,
        alpha=alpha,
        warnings=tuple(messages),
    )


def _time_column(frequencies: pd.DataFrame) -> str:
    if _TIME_SOURCE_COLUMN in frequencies.columns:
        return _TIME_SOURCE_COLUMN
    if "time" in frequencies.columns:
        return "time"
    raise ValueError(f"missing required column: {_TIME_SOURCE_COLUMN}")


def _validated_times(values: pd.Series) -> pd.Series:
    times = pd.to_numeric(values, errors="coerce")
    if times.isna().any() or (times < 0).any() or (times % 1 != 0).any():
        raise ValueError("time values must be non-negative integers")
    return times.astype(int)


def compare_response_by_time(
    frequencies: pd.DataFrame, *, alpha: float = config.ALPHA
) -> list[TimeComparison]:
    """Run sample-level response comparisons separately at each treatment time.

    Input columns are those required by `compare_response` plus
    `time_from_treatment_start` (or bundle-style alias `time`). Output is a list ordered
    by integer time; each item exposes `time` and a `comparison` whose DataFrame columns
    are exactly `config.RESPONSE_COMPARISON_COLUMNS`.
    """
    time_column = _time_column(frequencies)
    frame = frequencies.copy()
    frame[time_column] = _validated_times(frame[time_column])
    return [
        TimeComparison(
            time=int(time),
            comparison=compare_response(
                frame.loc[frame[time_column] == time], unit="sample", alpha=alpha
            ),
        )
        for time in sorted(frame[time_column].unique())
    ]


def distributions(frequencies: pd.DataFrame) -> list[dict[str, object]]:
    """Return bundle-ready raw percentage points for each population and response.

    Input columns are `sample, subject, response, population, percentage` plus
    `time_from_treatment_start` (or `time`); optional cohort columns are handled as in
    `compare_response`. Output entries have columns/keys `population, response, points`,
    where each point has `sample, subject, time, percentage`. Population, response,
    time, and sample ordering is deterministic.
    """
    time_column = _time_column(frequencies)
    frame = _cohort_frame(frequencies)
    frame[time_column] = _validated_times(frame[time_column])
    result: list[dict[str, object]] = []
    for population in config.POPULATIONS:
        for response in _GROUPS:
            group = frame.loc[
                (frame["population"] == population) & (frame["response"] == response),
                ["sample", "subject", time_column, "percentage"],
            ].sort_values([time_column, "sample"], kind="stable")
            points = [
                {
                    "sample": str(row.sample),
                    "subject": str(row.subject),
                    "time": int(getattr(row, time_column)),
                    "percentage": float(cast(float, row.percentage)),
                }
                for row in group.itertuples(index=False)
            ]
            result.append({"population": population, "response": response, "points": points})
    return result
