"""Compute deterministic long- and wide-form cell population frequencies."""

from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd

from immune_atlas import config

_INPUT_COLUMNS = ("sample", "population", "count")


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")


def compute_frequencies(counts_long: pd.DataFrame) -> pd.DataFrame:
    """Compute percentages from `sample, population, count` input rows.

    The input must contain exactly one non-negative count for every configured
    population in each sample. Additional columns are ignored. The returned columns
    are `sample, total_count, population, count, percentage`, in that exact order,
    sorted by sample and configured population order.
    """
    _require_columns(counts_long, _INPUT_COLUMNS)
    frame = counts_long.loc[:, list(_INPUT_COLUMNS)].copy()
    if frame.empty:
        return pd.DataFrame(columns=config.FREQUENCY_COLUMNS)
    if frame[["sample", "population", "count"]].isna().any().any():
        raise ValueError("sample, population, and count values must not be null")
    if frame.duplicated(subset=["sample", "population"]).any():
        raise ValueError("each sample and population pair must occur exactly once")

    unknown = sorted(set(frame["population"].astype(str)) - set(config.POPULATIONS))
    if unknown:
        raise ValueError(f"unknown populations: {', '.join(unknown)}")
    populations_per_sample = frame.groupby("sample", sort=False)["population"].nunique()
    if (populations_per_sample != len(config.POPULATIONS)).any():
        raise ValueError("every sample must contain each configured population exactly once")

    numeric_counts = pd.to_numeric(frame["count"], errors="coerce")
    if numeric_counts.isna().any() or not np.isfinite(numeric_counts.to_numpy(dtype=float)).all():
        raise ValueError("count values must be finite numbers")
    if (numeric_counts < 0).any():
        raise ValueError("count values must be non-negative")
    frame["count"] = numeric_counts
    frame["total_count"] = frame.groupby("sample", sort=False)["count"].transform("sum")
    if (frame["total_count"] <= 0).any():
        bad_samples = sorted(frame.loc[frame["total_count"] <= 0, "sample"].astype(str).unique())
        raise ValueError(f"sample total_count must be positive: {', '.join(bad_samples)}")
    frame["percentage"] = 100.0 * frame["count"] / frame["total_count"]

    sums = frame.groupby("sample", sort=False)["percentage"].sum().to_numpy(dtype=float)
    if not np.allclose(sums, 100.0, rtol=0.0, atol=1e-6):
        raise ValueError("population percentages must sum to 100 for every sample")
    order = {population: index for index, population in enumerate(config.POPULATIONS)}
    frame["_population_order"] = frame["population"].map(order)
    frame = frame.sort_values(["sample", "_population_order"], kind="stable")
    return frame.loc[:, list(config.FREQUENCY_COLUMNS)].reset_index(drop=True)


def to_wide(frequencies: pd.DataFrame) -> pd.DataFrame:
    """Pivot long frequencies into percentage columns for each population.

    Input columns are `sample, total_count, population, percentage`. Output columns
    are `sample, total_count` followed by the configured population names, whose
    values are percentages. Rows are sorted by sample.
    """
    required = ("sample", "total_count", "population", "percentage")
    _require_columns(frequencies, required)
    if frequencies.duplicated(subset=["sample", "population"]).any():
        raise ValueError("each sample and population pair must occur exactly once")
    totals_per_sample = frequencies.groupby("sample")["total_count"].nunique(dropna=False)
    if (totals_per_sample != 1).any():
        raise ValueError("total_count must be constant within a sample")

    wide = frequencies.pivot(index="sample", columns="population", values="percentage")
    missing = [population for population in config.POPULATIONS if population not in wide.columns]
    if missing:
        raise ValueError(f"missing configured populations: {', '.join(missing)}")
    wide = wide.loc[:, config.POPULATIONS].reset_index()
    totals = frequencies.groupby("sample", as_index=False, sort=True)["total_count"].first()
    output = totals.merge(wide, on="sample", how="inner", validate="one_to_one")
    return cast(
        pd.DataFrame,
        output.loc[:, ["sample", "total_count", *config.POPULATIONS]].reset_index(drop=True),
    )
