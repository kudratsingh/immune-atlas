from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from immune_atlas import config
from immune_atlas.analysis.frequencies import compute_frequencies, to_wide


def _counts() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for sample, counts in (
        ("sample-b", (20, 20, 20, 20, 20)),
        ("sample-a", (10, 20, 30, 15, 25)),
    ):
        rows.extend(
            {"sample": sample, "population": population, "count": count, "ignored": "x"}
            for population, count in zip(config.POPULATIONS, counts, strict=True)
        )
    return pd.DataFrame(rows)


def test_compute_frequencies_has_hand_computed_values_and_fixed_shape() -> None:
    result = compute_frequencies(_counts())

    assert tuple(result.columns) == config.FREQUENCY_COLUMNS
    assert list(result["sample"].unique()) == ["sample-a", "sample-b"]
    first = result.iloc[0]
    assert first.to_dict() == {
        "sample": "sample-a",
        "total_count": 100,
        "population": config.POPULATIONS[0],
        "count": 10,
        "percentage": 10.0,
    }
    assert np.allclose(result.groupby("sample")["percentage"].sum(), 100.0)
    assert result.groupby("sample").size().eq(len(config.POPULATIONS)).all()


def test_to_wide_returns_percentage_columns_in_configured_order() -> None:
    result = to_wide(compute_frequencies(_counts()))

    assert tuple(result.columns) == ("sample", "total_count", *config.POPULATIONS)
    assert result.loc[0, config.POPULATIONS].tolist() == [10.0, 20.0, 30.0, 15.0, 25.0]


def test_compute_frequencies_empty_input_has_fixed_columns() -> None:
    result = compute_frequencies(pd.DataFrame(columns=["sample", "population", "count"]))
    assert result.empty
    assert tuple(result.columns) == config.FREQUENCY_COLUMNS


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda frame: frame.drop(columns="count"), "missing required columns"),
        (lambda frame: pd.concat([frame, frame.iloc[[0]]]), "exactly once"),
        (lambda frame: frame.iloc[:-1], "each configured population"),
        (
            lambda frame: frame.assign(
                population=["unknown", *frame["population"].iloc[1:].tolist()]
            ),
            "unknown populations",
        ),
        (lambda frame: frame.assign(count=-1), "non-negative"),
        (lambda frame: frame.assign(count=np.nan), "must not be null"),
    ],
)
def test_compute_frequencies_rejects_invalid_input(mutator: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        compute_frequencies(mutator(_counts()))  # type: ignore[operator]


def test_compute_frequencies_rejects_zero_total() -> None:
    with pytest.raises(ValueError, match="total_count must be positive"):
        compute_frequencies(_counts().assign(count=0))


def test_to_wide_rejects_inconsistent_or_incomplete_rows() -> None:
    frequencies = compute_frequencies(_counts())
    duplicate = pd.concat([frequencies, frequencies.iloc[[0]]])
    with pytest.raises(ValueError, match="exactly once"):
        to_wide(duplicate)

    inconsistent = frequencies.copy()
    inconsistent.loc[0, "total_count"] = 999
    with pytest.raises(ValueError, match="constant"):
        to_wide(inconsistent)

    with pytest.raises(ValueError, match="missing configured"):
        to_wide(frequencies.loc[frequencies["population"] != config.POPULATIONS[-1]])
