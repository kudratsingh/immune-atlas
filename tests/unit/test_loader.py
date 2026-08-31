from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from immune_atlas.config import POPULATION_DISPLAY_NAMES, POPULATIONS
from immune_atlas.db.loader import init_db, load_csv, run
from immune_atlas.db.validate import DataContractError


def _write(frame: pd.DataFrame, path: Path) -> Path:
    frame.to_csv(path, index=False)
    return path


def test_small_csv_round_trips_into_normalised_tables(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    csv_path = _write(synthetic_wide_frame, tmp_path / "small.csv")
    db_path = tmp_path / "small.db"
    report = run(csv_path, db_path)

    assert report.table_counts == {
        "projects": 1,
        "subjects": 2,
        "samples": 2,
        "cell_populations": 5,
        "cell_counts": 10,
    }
    with sqlite3.connect(db_path) as connection:
        populations = connection.execute(
            "SELECT name, display_name, sort_order FROM cell_populations ORDER BY sort_order"
        ).fetchall()
        loaded_count = connection.execute("SELECT COUNT(*) FROM cell_counts").fetchone()[0]
    assert populations == [
        (population, POPULATION_DISPLAY_NAMES[population], order)
        for order, population in enumerate(POPULATIONS)
    ]
    assert loaded_count == 10


def test_run_is_byte_identical_and_count_identical_when_repeated(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    csv_path = _write(synthetic_wide_frame, tmp_path / "repeat.csv")
    db_path = tmp_path / "repeat.db"
    first = run(csv_path, db_path)
    first_bytes = db_path.read_bytes()
    second = run(csv_path, db_path)
    assert second.table_counts == first.table_counts
    assert db_path.read_bytes() == first_bytes


@pytest.mark.integration
def test_real_csv_loads_reference_row_counts(real_csv_path: Path, tmp_path: Path) -> None:
    report = run(real_csv_path, tmp_path / "real.db")
    assert report.projects == 3
    assert report.subjects == 3_500
    assert report.samples == 10_500
    assert report.populations == 5
    assert report.counts == 52_500
    assert report.seconds < 5


def test_load_csv_restores_journal_mode(synthetic_wide_frame: pd.DataFrame, tmp_path: Path) -> None:
    connection = init_db(tmp_path / "journal.db")
    try:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        load_csv(connection, _write(synthetic_wide_frame, tmp_path / "journal.csv"))
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    finally:
        connection.close()


def test_invalid_csv_is_rejected_before_any_rows_are_inserted(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    frame = synthetic_wide_frame.copy()
    frame.loc[0, "b_cell"] = -1
    connection = init_db(tmp_path / "invalid.db")
    try:
        with pytest.raises(DataContractError):
            load_csv(connection, _write(frame, tmp_path / "invalid.csv"))
        assert connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0
    finally:
        connection.close()


def test_init_db_replaces_existing_database(tmp_path: Path) -> None:
    db_path = tmp_path / "replace.db"
    first = init_db(db_path)
    first.execute("INSERT INTO projects VALUES ('temporary')")
    first.commit()
    first.close()
    second = init_db(db_path)
    try:
        assert second.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0
    finally:
        second.close()


def test_run_preserves_the_existing_database_when_validation_fails(
    synthetic_wide_frame: pd.DataFrame, tmp_path: Path
) -> None:
    db_path = tmp_path / "keep.db"
    run(_write(synthetic_wide_frame, tmp_path / "good.csv"), db_path)
    before = db_path.read_bytes()
    bad = synthetic_wide_frame.copy()
    bad.loc[0, "b_cell"] = -1
    with pytest.raises(DataContractError):
        run(_write(bad, tmp_path / "bad.csv"), db_path)
    assert db_path.read_bytes() == before
