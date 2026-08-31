from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from immune_atlas.config import POPULATIONS
from immune_atlas.db.validate import (
    REQUIRED_COLUMNS,
    DataContractError,
    read_validated_csv,
)


def _write(frame: pd.DataFrame, path: Path) -> Path:
    frame.to_csv(path, index=False)
    return path


def _problems(frame: pd.DataFrame, path: Path) -> tuple[tuple[int | None, str, str], ...]:
    with pytest.raises(DataContractError) as captured:
        read_validated_csv(_write(frame, path))
    return tuple((item.row, item.column, item.problem) for item in captured.value.problems)


def test_valid_csv_returns_typed_columns(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    result = read_validated_csv(_write(synthetic_wide_frame, tmp_path / "valid.csv"))
    assert tuple(result.columns) == REQUIRED_COLUMNS
    assert all(str(result[column].dtype) == "int64" for column in ("age", *POPULATIONS))
    assert result["response"].tolist() == ["yes", "no"]


def test_missing_required_column_is_reported(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    frame = synthetic_wide_frame.drop(columns="project")
    assert (None, "project", "required column is missing") in _problems(
        frame, tmp_path / "missing.csv"
    )


def test_expected_integer_type_is_enforced(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    frame = synthetic_wide_frame.copy()
    frame["age"] = frame["age"].astype("object")
    frame.loc[0, "age"] = "old"
    assert (2, "age", "must be an integer") in _problems(frame, tmp_path / "type.csv")


def test_sample_must_be_unique(synthetic_wide_frame: pd.DataFrame, tmp_path: Path) -> None:
    frame = synthetic_wide_frame.copy()
    frame.loc[1, "sample"] = frame.loc[0, "sample"]
    assert (3, "sample", "must be unique") in _problems(frame, tmp_path / "duplicate.csv")


@pytest.mark.parametrize("population", POPULATIONS)
def test_each_population_count_must_be_non_negative(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path, population: str
) -> None:
    frame = synthetic_wide_frame.copy()
    frame.loc[0, population] = -1
    assert (2, population, "must be non-negative") in _problems(
        frame, tmp_path / f"negative-{population}.csv"
    )


def test_total_count_must_be_positive(synthetic_wide_frame: pd.DataFrame, tmp_path: Path) -> None:
    frame = synthetic_wide_frame.copy()
    frame.loc[0, list(POPULATIONS)] = 0
    assert (2, "cell counts", "total count must be positive") in _problems(
        frame, tmp_path / "zero.csv"
    )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("sex", "X", "must be M or F"),
        ("response", "maybe", "must be yes, no, or null"),
        ("time_from_treatment_start", -1, "must be non-negative"),
    ],
)
def test_categorical_and_time_domains_are_enforced(
    synthetic_wide_frame: pd.DataFrame,
    tmp_path: Path,
    column: str,
    value: object,
    message: str,
) -> None:
    frame = synthetic_wide_frame.copy()
    frame.loc[0, column] = value
    assert (2, column, message) in _problems(frame, tmp_path / f"domain-{column}.csv")


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("project", "another-project"),
        ("condition", "carcinoma"),
        ("age", 99),
        ("sex", "M"),
        ("treatment", "phauximab"),
        ("response", "no"),
    ],
)
def test_subject_metadata_must_be_constant(
    synthetic_wide_frame: pd.DataFrame,
    tmp_path: Path,
    column: str,
    value: object,
) -> None:
    frame = pd.concat(
        [synthetic_wide_frame.iloc[[0]], synthetic_wide_frame.iloc[[0]]], ignore_index=True
    )
    frame.loc[1, "sample"] = "second-sample"
    frame.loc[1, "time_from_treatment_start"] = 7
    frame.loc[1, column] = value
    problems = _problems(frame, tmp_path / f"subject-{column}.csv")
    assert any(
        row == 3 and problem_column == column and "constant for subject" in problem
        for row, problem_column, problem in problems
    )


@pytest.mark.parametrize(
    ("treatment", "response", "message"),
    [
        ("none", "yes", "must be null when untreated"),
        ("miraclib", None, "must be yes or no when treated"),
    ],
)
def test_response_nullability_matches_treatment(
    synthetic_wide_frame: pd.DataFrame,
    tmp_path: Path,
    treatment: str,
    response: str | None,
    message: str,
) -> None:
    frame = synthetic_wide_frame.iloc[[0]].copy()
    frame.loc[frame.index[0], "treatment"] = treatment
    frame.loc[frame.index[0], "response"] = response
    assert (2, "response", message) in _problems(frame, tmp_path / "response.csv")


def test_unknown_population_is_rejected(synthetic_wide_frame: pd.DataFrame, tmp_path: Path) -> None:
    frame = synthetic_wide_frame.assign(eosinophil=1)
    assert (None, "eosinophil", "unknown column or cell population") in _problems(
        frame, tmp_path / "unknown.csv"
    )


def test_duplicate_subject_sample_type_time_is_rejected(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    frame = pd.concat(
        [synthetic_wide_frame.iloc[[0]], synthetic_wide_frame.iloc[[0]]], ignore_index=True
    )
    frame.loc[1, "sample"] = "different-sample"
    problems = _problems(frame, tmp_path / "duplicate-key.csv")
    assert any("combination must be unique" in problem for _, _, problem in problems)


def test_multiple_problems_are_collected_in_one_error(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    frame = synthetic_wide_frame.copy()
    frame.loc[0, "sex"] = "X"
    frame.loc[1, "b_cell"] = -1
    frame["mystery_cell"] = 10
    problems = _problems(frame, tmp_path / "multiple.csv")
    assert {column for _, column, _ in problems} >= {"sex", "b_cell", "mystery_cell"}
    assert len(problems) >= 3


def test_empty_and_missing_files_fail_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="input CSV not found"):
        read_validated_csv(tmp_path / "missing.csv")
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(DataContractError) as captured:
        read_validated_csv(empty)
    assert len(captured.value.problems) == len(REQUIRED_COLUMNS)
