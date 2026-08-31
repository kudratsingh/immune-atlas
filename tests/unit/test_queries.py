from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest

from immune_atlas.config import FREQUENCY_COLUMNS, POPULATIONS, RESPONSE_COHORT
from immune_atlas.db.connection import connect
from immune_atlas.db.loader import run
from immune_atlas.db.queries import (
    baseline_breakdown,
    baseline_samples,
    cell_frequencies,
    cohort_frequencies,
    form_answer,
)


@pytest.fixture(scope="module")
def real_connection(tmp_path_factory: pytest.TempPathFactory) -> Iterator[sqlite3.Connection]:
    repo_root = Path(__file__).resolve().parents[2]
    db_path = tmp_path_factory.mktemp("queries") / "real.db"
    run(repo_root / "data" / "cell-count.csv", db_path)
    connection = connect(db_path)
    yield connection
    connection.close()


def test_cell_frequencies_has_fixed_columns_values_and_order(
    real_connection: sqlite3.Connection,
) -> None:
    frame = cell_frequencies(real_connection)
    assert tuple(frame.columns) == FREQUENCY_COLUMNS
    assert len(frame) == 52_500
    assert frame.iloc[:5]["sample"].tolist() == ["sample00000"] * 5
    assert frame.iloc[:5]["population"].tolist() == list(POPULATIONS)
    assert frame.iloc[:5]["count"].tolist() == [10908, 24440, 20491, 13864, 23511]
    assert frame.iloc[:5]["total_count"].tolist() == [93_214] * 5
    assert frame.iloc[:5]["percentage"].sum() == pytest.approx(100.0)
    assert frame["sample"].is_monotonic_increasing


def test_response_cohort_query_returns_reference_sample_and_subject_counts(
    real_connection: sqlite3.Connection,
) -> None:
    frame = cohort_frequencies(
        real_connection,
        condition=RESPONSE_COHORT.condition,
        treatment=RESPONSE_COHORT.treatment,
        sample_type=RESPONSE_COHORT.sample_type,
    )
    assert len(frame) == 1_968 * len(POPULATIONS)
    assert frame["sample"].nunique() == 1_968
    assert frame["subject"].nunique() == 656
    assert frame.loc[frame["response"] == "yes", "sample"].nunique() == 993
    assert frame.loc[frame["response"] == "no", "sample"].nunique() == 975
    assert frame["sample"].is_monotonic_increasing


def test_baseline_samples_and_sql_breakdowns_match_reference_numbers(
    real_connection: sqlite3.Connection,
) -> None:
    filters = {
        "condition": RESPONSE_COHORT.condition,
        "treatment": RESPONSE_COHORT.treatment,
        "sample_type": RESPONSE_COHORT.sample_type,
        "time": 0,
    }
    samples = baseline_samples(real_connection, **filters)
    breakdown = baseline_breakdown(real_connection, **filters)
    assert len(samples) == 656
    assert samples["subject"].nunique() == 656
    pd.testing.assert_frame_equal(
        breakdown.by_project,
        pd.DataFrame({"project": ["prj1", "prj3"], "n_samples": [384, 272]}),
    )
    pd.testing.assert_frame_equal(
        breakdown.by_response,
        pd.DataFrame({"response": ["yes", "no"], "n_subjects": [331, 325]}),
    )
    pd.testing.assert_frame_equal(
        breakdown.by_sex,
        pd.DataFrame({"sex": ["M", "F"], "n_subjects": [344, 312]}),
    )


def test_form_answer_matches_raw_b_cell_reference(real_connection: sqlite3.Connection) -> None:
    matching_samples = real_connection.execute(
        """
        SELECT COUNT(*)
        FROM samples AS s
        JOIN subjects AS u ON u.subject_id = s.subject_id
        WHERE u.condition = 'melanoma' AND u.sex = 'M' AND u.response = 'yes'
          AND s.time_from_treatment_start = 0
        """
    ).fetchone()[0]
    assert matching_samples == 485
    assert form_answer(real_connection) == 10_206.15


def test_form_answer_raises_when_cohort_is_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"
    repo_root = Path(__file__).resolve().parents[2]
    schema = repo_root / "immune_atlas" / "db" / "schema.sql"
    connection = connect(db_path)
    try:
        connection.executescript(schema.read_text(encoding="utf-8"))
        with pytest.raises(LookupError, match="contains no B-cell counts"):
            form_answer(connection)
    finally:
        connection.close()
