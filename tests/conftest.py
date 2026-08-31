"""Shared pytest fixtures for repository, tabular, and real-data tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def real_csv_path() -> Path:
    return REPO_ROOT / "data" / "cell-count.csv"


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    destination = tmp_path / "immune-atlas"
    shutil.copytree(
        REPO_ROOT,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".coverage",
            "coverage.xml",
            "*.egg-info",
            "__pycache__",
            "*.pyc",
        ),
    )
    return destination


@pytest.fixture
def synthetic_wide_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "project": "prj-test",
                "subject": "subject-yes",
                "condition": "melanoma",
                "age": 48,
                "sex": "F",
                "treatment": "miraclib",
                "response": "yes",
                "sample": "sample-yes",
                "sample_type": "PBMC",
                "time_from_treatment_start": 0,
                "b_cell": 10,
                "cd8_t_cell": 20,
                "cd4_t_cell": 30,
                "nk_cell": 15,
                "monocyte": 25,
            },
            {
                "project": "prj-test",
                "subject": "subject-no",
                "condition": "melanoma",
                "age": 51,
                "sex": "M",
                "treatment": "miraclib",
                "response": "no",
                "sample": "sample-no",
                "sample_type": "PBMC",
                "time_from_treatment_start": 0,
                "b_cell": 20,
                "cd8_t_cell": 10,
                "cd4_t_cell": 25,
                "nk_cell": 20,
                "monocyte": 25,
            },
        ]
    )


@pytest.fixture
def synthetic_long_frame(synthetic_wide_frame: pd.DataFrame) -> pd.DataFrame:
    from immune_atlas.config import POPULATIONS

    metadata = [column for column in synthetic_wide_frame.columns if column not in POPULATIONS]
    return synthetic_wide_frame.melt(
        id_vars=metadata,
        value_vars=POPULATIONS,
        var_name="population",
        value_name="count",
    )
