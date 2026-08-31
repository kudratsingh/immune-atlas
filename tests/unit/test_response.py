from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from immune_atlas import config
from immune_atlas.analysis.response import (
    compare_response,
    compare_response_by_time,
    distributions,
)


def _response_frame(n_per_group: int = 16, *, shifted: bool = True) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for response in ("yes", "no"):
        for subject_index in range(n_per_group):
            subject = f"{response}-{subject_index:02d}"
            for time in (0, 7, 14):
                sample = f"{subject}-{time:02d}"
                for population_index, population in enumerate(config.POPULATIONS):
                    base = 20.0 + population_index + subject_index * 0.01 + time * 0.001
                    if shifted and population == config.POPULATIONS[2]:
                        base += 20.0 if response == "yes" else -20.0
                    rows.append(
                        {
                            "sample": sample,
                            "subject": subject,
                            "condition": config.RESPONSE_COHORT.condition,
                            "treatment": config.RESPONSE_COHORT.treatment,
                            "sample_type": config.RESPONSE_COHORT.sample_type,
                            "response": response,
                            "time_from_treatment_start": time,
                            "population": population,
                            "percentage": base,
                        }
                    )
    return pd.DataFrame(rows)


def test_planted_shift_is_adjusted_significant_with_positive_effect() -> None:
    result = compare_response(_response_frame(), unit="sample")
    target = result.table.set_index("population").loc[config.POPULATIONS[2]]
    other = result.table.loc[result.table["population"] != config.POPULATIONS[2]]

    assert tuple(result.table.columns) == config.RESPONSE_COMPARISON_COLUMNS
    assert result.rows is result.table
    assert result.unit == "sample"
    assert result.n_samples == 96
    assert result.n_subjects == 32
    assert target["significant_adjusted"]
    assert target["effect_size"] > 0.99
    assert not other["significant_adjusted"].any()
    ordered = result.table.dropna(subset=["p_value"]).sort_values("p_value")
    assert ordered["q_value"].is_monotonic_increasing


def test_null_case_has_no_significant_populations() -> None:
    result = compare_response(_response_frame(shifted=False))
    assert not result.table["significant_raw"].any()
    assert not result.table["significant_adjusted"].any()
    assert np.allclose(result.table["effect_size"], 0.0)
    assert result.table["welch_p"].notna().all()


def test_subject_analysis_collapses_three_samples_per_subject() -> None:
    result = compare_response(_response_frame(), unit="subject")
    assert result.n_samples == 96
    assert result.n_subjects == 32
    assert result.table["n_yes"].eq(16).all()
    assert result.table["n_no"].eq(16).all()


def test_degenerate_groups_emit_warning_and_null_statistics() -> None:
    result = compare_response(_response_frame(n_per_group=2))
    assert result.table["n_yes"].eq(6).all()
    assert result.table["n_no"].eq(6).all()
    # Pooled sample groups are valid; each time slice is intentionally degenerate.
    with pytest.warns(RuntimeWarning) as caught:
        by_time = compare_response_by_time(_response_frame(n_per_group=2))
    assert len(caught) == 3 * len(config.POPULATIONS)
    first = by_time[0].comparison.table
    assert len(by_time[0].comparison.warnings) == len(config.POPULATIONS)
    assert first["n_yes"].eq(2).all()
    assert first["p_value"].isna().all()
    assert first["mean_yes"].isna().all()
    assert not first["significant_adjusted"].any()


def test_time_comparisons_and_distributions_are_deterministically_ordered() -> None:
    frame = _response_frame(n_per_group=3).sample(frac=1.0, random_state=4)
    by_time = compare_response_by_time(frame)
    raw = distributions(frame)

    assert [item.time for item in by_time] == [0, 7, 14]
    assert all(item.comparison.unit == "sample" for item in by_time)
    assert [(item["population"], item["response"]) for item in raw[:2]] == [
        (config.POPULATIONS[0], "yes"),
        (config.POPULATIONS[0], "no"),
    ]
    points = raw[0]["points"]
    assert isinstance(points, list)
    assert list(points[0]) == ["sample", "subject", "time", "percentage"]
    assert [point["time"] for point in points] == sorted(point["time"] for point in points)


def test_optional_metadata_filters_to_the_fixed_response_cohort() -> None:
    frame = _response_frame(n_per_group=3)
    excluded = frame.copy()
    excluded["condition"] = "other"
    result = compare_response(pd.concat([excluded, frame], ignore_index=True))
    assert result.n_samples == 18


@pytest.mark.parametrize(
    ("frame", "kwargs", "message"),
    [
        (_response_frame(3).drop(columns="subject"), {}, "missing required columns"),
        (_response_frame(3).drop(columns="sample_type"), {}, "must be supplied together"),
        (_response_frame(3).assign(percentage=np.nan), {}, "finite numbers"),
        (_response_frame(3).assign(response=None), {}, "contains no"),
        (_response_frame(3), {"unit": "visit"}, "unit must be"),
        (_response_frame(3), {"alpha": 2.0}, "alpha must be"),
    ],
)
def test_compare_response_rejects_invalid_inputs(
    frame: pd.DataFrame, kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        compare_response(frame, **kwargs)  # type: ignore[arg-type]


def test_response_rejects_duplicates_unknown_populations_and_subject_conflicts() -> None:
    frame = _response_frame(3)
    with pytest.raises(ValueError, match="exactly once"):
        compare_response(pd.concat([frame, frame.iloc[[0]]]))

    unknown = frame.copy()
    unknown.loc[0, "population"] = "unknown"
    with pytest.raises(ValueError, match="unknown populations"):
        compare_response(unknown)

    conflict = frame.copy()
    subject = conflict.loc[0, "subject"]
    conflict.loc[(conflict["subject"] == subject) & (conflict.index == 0), "response"] = "no"
    with pytest.raises(ValueError, match="constant"):
        compare_response(conflict)


def test_time_functions_accept_time_alias_and_reject_bad_values() -> None:
    frame = _response_frame(3).rename(columns={"time_from_treatment_start": "time"})
    assert [item.time for item in compare_response_by_time(frame)] == [0, 7, 14]
    assert distributions(frame)[0]["points"]

    with pytest.raises(ValueError, match="missing required column"):
        compare_response_by_time(frame.drop(columns="time"))
    with pytest.raises(ValueError, match="non-negative integers"):
        compare_response_by_time(frame.assign(time=-1))
    with pytest.raises(ValueError, match="non-negative integers"):
        distributions(frame.assign(time=0.5))
