"""Rebuild the normalised SQLite database from a validated wide CSV."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pandas as pd

from immune_atlas.config import POPULATION_DISPLAY_NAMES, POPULATIONS
from immune_atlas.db.connection import bulk_load_mode, connect
from immune_atlas.db.validate import read_validated_csv
from immune_atlas.observability import get_logger

_SCHEMA_PATH: Final = Path(__file__).with_name("schema.sql")
_LOGGER = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class LoadReport:
    """Summarise rows loaded into each table and elapsed wall time."""

    projects: int
    subjects: int
    samples: int
    populations: int
    counts: int
    seconds: float

    @property
    def table_counts(self) -> dict[str, int]:
        """Return table row counts keyed by schema table name."""
        return {
            "projects": self.projects,
            "subjects": self.subjects,
            "samples": self.samples,
            "cell_populations": self.populations,
            "cell_counts": self.counts,
        }


def _as_int(value: object) -> int:
    return int(str(value))


def init_db(db_path: Path) -> sqlite3.Connection:
    """Replace any existing database with a fresh copy of the fixed schema."""
    if db_path.exists():
        db_path.unlink()
    connection = connect(db_path)
    try:
        connection.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    except Exception:
        connection.close()
        raise
    return connection


def _subject_rows(frame: pd.DataFrame) -> list[tuple[object, ...]]:
    columns = ["subject", "project", "condition", "age", "sex", "treatment", "response"]
    subjects = frame.loc[:, columns].drop_duplicates(subset=["subject"]).sort_values("subject")
    return [
        (
            row.subject,
            row.project,
            row.condition,
            _as_int(row.age),
            row.sex,
            row.treatment,
            None if pd.isna(row.response) else row.response,
        )
        for row in subjects.itertuples(index=False)
    ]


def _sample_rows(frame: pd.DataFrame) -> list[tuple[object, ...]]:
    samples = frame.sort_values("sample")
    return [
        (row.sample, row.subject, row.sample_type, _as_int(row.time_from_treatment_start))
        for row in samples.itertuples(index=False)
    ]


def _count_rows(frame: pd.DataFrame) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for sample in frame.sort_values("sample").itertuples(index=False):
        for population_id, population in enumerate(POPULATIONS, start=1):
            rows.append((sample.sample, population_id, int(getattr(sample, population))))
    return rows


def load_csv(connection: sqlite3.Connection, csv_path: Path) -> LoadReport:
    """Validate and insert one wide CSV into an empty initialised database."""
    started_at = time.perf_counter()
    return _insert_frame(connection, read_validated_csv(csv_path), started_at)


def _insert_frame(
    connection: sqlite3.Connection, frame: pd.DataFrame, started_at: float
) -> LoadReport:
    projects = sorted(str(project) for project in frame["project"].unique())
    subject_rows = _subject_rows(frame)
    sample_rows = _sample_rows(frame)
    population_rows = [
        (position, population, POPULATION_DISPLAY_NAMES[population], position - 1)
        for position, population in enumerate(POPULATIONS, start=1)
    ]
    count_rows = _count_rows(frame)

    with bulk_load_mode(connection), connection:
        connection.executemany("INSERT INTO projects VALUES (?)", [(item,) for item in projects])
        connection.executemany("INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?, ?)", subject_rows)
        connection.executemany("INSERT INTO samples VALUES (?, ?, ?, ?)", sample_rows)
        connection.executemany("INSERT INTO cell_populations VALUES (?, ?, ?, ?)", population_rows)
        connection.executemany("INSERT INTO cell_counts VALUES (?, ?, ?)", count_rows)

    report = LoadReport(
        projects=len(projects),
        subjects=len(subject_rows),
        samples=len(sample_rows),
        populations=len(population_rows),
        counts=len(count_rows),
        seconds=time.perf_counter() - started_at,
    )
    _LOGGER.info(
        "database_loaded projects=%d subjects=%d samples=%d populations=%d counts=%d seconds=%.6f",
        report.projects,
        report.subjects,
        report.samples,
        report.populations,
        report.counts,
        report.seconds,
    )
    return report


def run(csv_path: Path, db_path: Path) -> LoadReport:
    """Validate the CSV, then rebuild a database from scratch (ARCHITECTURE §Loading).

    Validation runs before the existing database file is touched, so an invalid
    input leaves the previous database in place.
    """
    started_at = time.perf_counter()
    frame = read_validated_csv(csv_path)
    connection = init_db(db_path)
    try:
        return _insert_frame(connection, frame, started_at)
    finally:
        connection.close()
