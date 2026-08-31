from __future__ import annotations

import pandas as pd
import pytest

from immune_atlas.analysis.subsets import summarise_baseline


def _samples() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sample": "sample-c",
                "subject": "subject-1",
                "project": "prj1",
                "response": "yes",
                "sex": "F",
            },
            {
                "sample": "sample-a",
                "subject": "subject-1",
                "project": "prj1",
                "response": "yes",
                "sex": "F",
            },
            {
                "sample": "sample-b",
                "subject": "subject-2",
                "project": "prj1",
                "response": "no",
                "sex": "M",
            },
        ]
    )


def test_baseline_counts_projects_by_sample_and_groups_by_subject() -> None:
    result = summarise_baseline(_samples())

    assert result.n_samples == 3
    assert result.n_subjects == 2
    assert result.by_project.to_dict("records") == [{"project": "prj1", "n_samples": 3}]
    assert result.by_response.to_dict("records") == [
        {"response": "no", "n_subjects": 1},
        {"response": "yes", "n_subjects": 1},
    ]
    assert result.by_sex.to_dict("records") == [
        {"sex": "F", "n_subjects": 1},
        {"sex": "M", "n_subjects": 1},
    ]
    assert result.sample_ids == ("sample-a", "sample-b", "sample-c")


def test_baseline_rejects_missing_null_or_duplicate_samples() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        summarise_baseline(_samples().drop(columns="sex"))
    with pytest.raises(ValueError, match="must not contain null"):
        summarise_baseline(_samples().assign(response=None))
    with pytest.raises(ValueError, match="one row per sample"):
        summarise_baseline(pd.concat([_samples(), _samples().iloc[[0]]]))


@pytest.mark.parametrize("column", ["project", "response", "sex"])
def test_baseline_rejects_conflicting_subject_metadata(column: str) -> None:
    frame = _samples()
    frame.loc[1, column] = f"different-{column}"
    with pytest.raises(ValueError, match=f"{column} must be constant"):
        summarise_baseline(frame)
