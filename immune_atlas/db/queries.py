"""Expose deterministic SQLite read queries as pandas DataFrames and scalars."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from immune_atlas.config import BASELINE_TIME, FREQUENCY_COLUMNS, POPULATIONS


@dataclass(frozen=True, slots=True)
class BaselineBreakdown:
    """Hold SQL-derived project, response, and sex baseline aggregations."""

    by_project: pd.DataFrame
    by_response: pd.DataFrame
    by_sex: pd.DataFrame


def _frame(
    connection: sqlite3.Connection,
    sql: str,
    parameters: Sequence[object] = (),
) -> pd.DataFrame:
    cursor = connection.execute(sql, parameters)
    columns = [description[0] for description in cursor.description or ()]
    return pd.DataFrame.from_records(cursor.fetchall(), columns=columns)


def cell_frequencies(connection: sqlite3.Connection) -> pd.DataFrame:
    """Return `sample,total_count,population,count,percentage` for every count row."""
    frame = _frame(
        connection,
        """
        SELECT f.sample, f.total_count, f.population, f.count, f.percentage
        FROM v_cell_frequencies AS f
        JOIN cell_populations AS p ON p.name = f.population
        ORDER BY f.sample, p.sort_order
        """,
    )
    return frame.loc[:, list(FREQUENCY_COLUMNS)]


def sample_metadata(connection: sqlite3.Connection) -> pd.DataFrame:
    """Return one row per sample with subject metadata and the sample total count.

    Columns are `sample, subject, project, condition, age, sex, treatment, response,
    sample_type, time_from_treatment_start, total_count`, ordered by sample.
    """
    return _frame(
        connection,
        """
        SELECT s.sample_id AS sample,
               s.subject_id AS subject,
               u.project_id AS project,
               u.condition,
               u.age,
               u.sex,
               u.treatment,
               u.response,
               s.sample_type,
               s.time_from_treatment_start,
               t.total_count
        FROM samples AS s
        JOIN subjects AS u ON u.subject_id = s.subject_id
        JOIN v_sample_totals AS t ON t.sample_id = s.sample_id
        ORDER BY s.sample_id
        """,
    )


def cohort_frequencies(
    connection: sqlite3.Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
) -> pd.DataFrame:
    """Return cohort metadata followed by total, population, count, and percentage columns."""
    return _frame(
        connection,
        """
        SELECT f.sample,
               s.subject_id AS subject,
               u.project_id AS project,
               u.condition,
               u.age,
               u.sex,
               u.treatment,
               u.response,
               s.sample_type,
               s.time_from_treatment_start,
               f.total_count,
               f.population,
               f.count,
               f.percentage
        FROM v_cell_frequencies AS f
        JOIN samples AS s ON s.sample_id = f.sample
        JOIN subjects AS u ON u.subject_id = s.subject_id
        JOIN cell_populations AS p ON p.name = f.population
        WHERE u.condition = ? AND u.treatment = ? AND s.sample_type = ?
        ORDER BY f.sample, p.sort_order
        """,
        (condition, treatment, sample_type),
    )


def baseline_samples(
    connection: sqlite3.Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
    time: int = BASELINE_TIME,
) -> pd.DataFrame:
    """Return project-through-response and sample-through-time columns for Part 4."""
    return _frame(
        connection,
        """
        SELECT u.project_id AS project,
               u.subject_id AS subject,
               u.condition,
               u.age,
               u.sex,
               u.treatment,
               u.response,
               s.sample_id AS sample,
               s.sample_type,
               s.time_from_treatment_start
        FROM samples AS s
        JOIN subjects AS u ON u.subject_id = s.subject_id
        WHERE u.condition = ?
          AND u.treatment = ?
          AND s.sample_type = ?
          AND s.time_from_treatment_start = ?
        ORDER BY s.sample_id
        """,
        (condition, treatment, sample_type, time),
    )


def baseline_breakdown(
    connection: sqlite3.Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
    time: int = BASELINE_TIME,
) -> BaselineBreakdown:
    """Return project/n_samples plus response-or-sex/n_subjects SQL frames."""
    parameters = (condition, treatment, sample_type, time)
    joins_and_filter = """
        FROM samples AS s
        JOIN subjects AS u ON u.subject_id = s.subject_id
        WHERE u.condition = ?
          AND u.treatment = ?
          AND s.sample_type = ?
          AND s.time_from_treatment_start = ?
    """
    by_project = _frame(
        connection,
        "SELECT u.project_id AS project, COUNT(*) AS n_samples "
        f"{joins_and_filter} GROUP BY u.project_id ORDER BY u.project_id",
        parameters,
    )
    by_response = _frame(
        connection,
        "SELECT u.response, COUNT(DISTINCT u.subject_id) AS n_subjects "
        f"{joins_and_filter} AND u.response IS NOT NULL "
        "GROUP BY u.response ORDER BY CASE u.response WHEN 'yes' THEN 0 ELSE 1 END",
        parameters,
    )
    by_sex = _frame(
        connection,
        "SELECT u.sex, COUNT(DISTINCT u.subject_id) AS n_subjects "
        f"{joins_and_filter} "
        "GROUP BY u.sex ORDER BY CASE u.sex WHEN 'M' THEN 0 ELSE 1 END",
        parameters,
    )
    return BaselineBreakdown(
        by_project=by_project,
        by_response=by_response,
        by_sex=by_sex,
    )


def form_answer(connection: sqlite3.Connection) -> float:
    """Return the two-decimal mean raw B-cell count for the assignment form cohort."""
    row = connection.execute(
        """
        SELECT ROUND(AVG(c.count), 2) AS mean_b_cell
        FROM cell_counts AS c
        JOIN cell_populations AS p ON p.population_id = c.population_id
        JOIN samples AS s ON s.sample_id = c.sample_id
        JOIN subjects AS u ON u.subject_id = s.subject_id
        WHERE p.name = ?
          AND u.condition = 'melanoma'
          AND u.sex = 'M'
          AND u.response = 'yes'
          AND s.time_from_treatment_start = ?
        """,
        (POPULATIONS[0], BASELINE_TIME),
    ).fetchone()
    if row is None or row["mean_b_cell"] is None:
        raise LookupError("form-answer cohort contains no B-cell counts")
    return float(row["mean_b_cell"])
