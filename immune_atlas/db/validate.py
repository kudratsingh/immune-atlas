"""Validate the wide source CSV and report every data-contract problem together."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

from immune_atlas.config import POPULATIONS

SUBJECT_COLUMNS: Final = (
    "project",
    "subject",
    "condition",
    "age",
    "sex",
    "treatment",
    "response",
)
SAMPLE_COLUMNS: Final = ("sample", "sample_type", "time_from_treatment_start")
REQUIRED_COLUMNS: Final = (*SUBJECT_COLUMNS, *SAMPLE_COLUMNS, *POPULATIONS)
_REQUIRED_TEXT_COLUMNS: Final = (
    "project",
    "subject",
    "condition",
    "sex",
    "treatment",
    "sample",
    "sample_type",
)
_INTEGER_COLUMNS: Final = ("age", "time_from_treatment_start", *POPULATIONS)
_INTEGER_PATTERN: Final = re.compile(r"[+-]?\d+")


@dataclass(frozen=True, slots=True)
class DataProblem:
    """Identify one invalid source location and explain the violation."""

    row: int | None
    column: str
    problem: str


class DataContractError(ValueError):
    """Report all validation problems discovered in one source file."""

    def __init__(self, problems: Iterable[DataProblem]) -> None:
        """Store non-empty validation problems and render a reviewer-friendly message."""
        self.problems = tuple(problems)
        if not self.problems:
            raise ValueError("DataContractError requires at least one problem")
        details = "\n".join(
            f"- {'file' if item.row is None else f'row {item.row}'}, "
            f"column {item.column!r}: {item.problem}"
            for item in self.problems
        )
        summary = f"CSV data contract failed with {len(self.problems)} problem(s)"
        super().__init__(f"{summary}:\n{details}")


def _is_missing(value: object) -> bool:
    if value is None or value is pd.NA or value is pd.NaT:
        return True
    return isinstance(value, float) and math.isnan(value)


def _text(value: object) -> str | None:
    if _is_missing(value):
        return None
    rendered = str(value).strip()
    return rendered or None


def _integer(value: object) -> int | None:
    if isinstance(value, bool) or _is_missing(value):
        return None
    if isinstance(value, int):
        return value
    rendered = str(value).strip()
    if _INTEGER_PATTERN.fullmatch(rendered) is None:
        return None
    return int(rendered)


def _source_row(position: int) -> int:
    return position + 2


def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return typed columns in source order, or raise with all invariant violations."""
    source = frame.reset_index(drop=True)
    problems: list[DataProblem] = []
    available = {str(column) for column in source.columns}

    for column in REQUIRED_COLUMNS:
        if column not in available:
            problems.append(DataProblem(None, column, "required column is missing"))
    for column in source.columns:
        name = str(column)
        if name not in REQUIRED_COLUMNS:
            problems.append(DataProblem(None, name, "unknown column or cell population"))

    source_values = {
        column: source[column].tolist() if column in source else [None] * len(source)
        for column in REQUIRED_COLUMNS
    }
    normalized: dict[str, list[object]] = {column: [] for column in REQUIRED_COLUMNS}
    for position in range(len(source)):
        row_number = _source_row(position)
        for column in _REQUIRED_TEXT_COLUMNS:
            text_value = _text(source_values[column][position])
            normalized[column].append(text_value)
            if text_value is None and column in available:
                problems.append(DataProblem(row_number, column, "must be non-empty text"))

        response = _text(source_values["response"][position])
        normalized["response"].append(response)
        if response is not None and response not in {"yes", "no"}:
            problems.append(DataProblem(row_number, "response", "must be yes, no, or null"))

        for column in _INTEGER_COLUMNS:
            raw_value = source_values[column][position]
            integer_value = _integer(raw_value)
            normalized[column].append(integer_value)
            if column in available and integer_value is None:
                problems.append(DataProblem(row_number, column, "must be an integer"))
            elif integer_value is not None and integer_value < 0:
                problems.append(DataProblem(row_number, column, "must be non-negative"))

        treatment = normalized["treatment"][-1]
        if treatment == "none" and response is not None:
            problems.append(DataProblem(row_number, "response", "must be null when untreated"))
        elif treatment is not None and treatment != "none" and response is None:
            problems.append(DataProblem(row_number, "response", "must be yes or no when treated"))

        counts = [normalized[population][-1] for population in POPULATIONS]
        valid_counts = [count for count in counts if isinstance(count, int) and count >= 0]
        if len(valid_counts) == len(POPULATIONS) and sum(valid_counts) == 0:
            problems.append(DataProblem(row_number, "cell counts", "total count must be positive"))

    if "sex" in available:
        for position, sex in enumerate(normalized["sex"]):
            if sex is not None and sex not in {"M", "F"}:
                problems.append(DataProblem(_source_row(position), "sex", "must be M or F"))

    if "sample" in available:
        seen_samples: dict[object, int] = {}
        for position, sample in enumerate(normalized["sample"]):
            if sample is None:
                continue
            if sample in seen_samples:
                problems.append(DataProblem(_source_row(position), "sample", "must be unique"))
            else:
                seen_samples[sample] = position

    unique_sample_keys: dict[tuple[object, object, object], int] = {}
    for position, key in enumerate(
        zip(
            normalized["subject"],
            normalized["sample_type"],
            normalized["time_from_treatment_start"],
            strict=True,
        )
    ):
        if None in key:
            continue
        if key in unique_sample_keys:
            problems.append(
                DataProblem(
                    _source_row(position),
                    "subject/sample_type/time_from_treatment_start",
                    "combination must be unique",
                )
            )
        else:
            unique_sample_keys[key] = position

    first_subject_values: dict[tuple[object, str], object] = {}
    for position, subject in enumerate(normalized["subject"]):
        if subject is None:
            continue
        for column in SUBJECT_COLUMNS:
            if column == "subject":
                continue
            subject_value = normalized[column][position]
            subject_key = (subject, column)
            if subject_key not in first_subject_values:
                first_subject_values[subject_key] = subject_value
            elif subject_value != first_subject_values[subject_key]:
                problems.append(
                    DataProblem(
                        _source_row(position),
                        column,
                        f"must be constant for subject {subject!r}",
                    )
                )

    if problems:
        raise DataContractError(problems)

    result = pd.DataFrame(normalized, columns=REQUIRED_COLUMNS)
    for column in _INTEGER_COLUMNS:
        result[column] = result[column].astype("int64")
    return result


def read_validated_csv(csv_path: Path) -> pd.DataFrame:
    """Read a source CSV with explicit string dtypes and return validated typed rows."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"input CSV not found: {csv_path}; run from the repository root")
    try:
        frame = pd.read_csv(
            csv_path,
            dtype="string",
            keep_default_na=False,
            na_values=[""],
        )
    except pd.errors.EmptyDataError as error:
        raise DataContractError(
            DataProblem(None, column, "required column is missing") for column in REQUIRED_COLUMNS
        ) from error
    return validate_frame(frame)
