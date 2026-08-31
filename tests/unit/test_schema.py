from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from immune_atlas.db.loader import init_db


@pytest.fixture
def schema_connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = init_db(tmp_path / "schema.db")
    yield connection
    connection.close()


def _insert_parent_rows(connection: sqlite3.Connection) -> None:
    connection.execute("INSERT INTO projects VALUES ('project-1')")
    connection.execute(
        "INSERT INTO subjects VALUES "
        "('subject-1', 'project-1', 'melanoma', 50, 'F', 'miraclib', 'yes')"
    )
    connection.execute("INSERT INTO samples VALUES ('sample-1', 'subject-1', 'PBMC', 0)")
    connection.execute("INSERT INTO cell_populations VALUES (1, 'b_cell', 'B cells', 0)")
    connection.commit()


def test_schema_creates_every_table_index_and_view(schema_connection: sqlite3.Connection) -> None:
    objects = {
        (row["type"], row["name"])
        for row in schema_connection.execute(
            "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        )
    }
    assert {
        ("table", "projects"),
        ("table", "subjects"),
        ("table", "samples"),
        ("table", "cell_populations"),
        ("table", "cell_counts"),
        ("view", "v_sample_totals"),
        ("view", "v_cell_frequencies"),
    } <= objects
    assert {
        "idx_subjects_project",
        "idx_subjects_cohort",
        "idx_samples_subject",
        "idx_samples_type_time",
        "idx_counts_population",
    } <= {name for object_type, name in objects if object_type == "index"}


def test_connection_enforces_foreign_keys(schema_connection: sqlite3.Connection) -> None:
    assert schema_connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        schema_connection.execute(
            "INSERT INTO subjects VALUES "
            "('orphan', 'missing', 'melanoma', 50, 'M', 'miraclib', 'yes')"
        )


@pytest.mark.parametrize(
    ("statement", "parameters"),
    [
        (
            "INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("bad-age", "project-1", "melanoma", -1, "M", "miraclib", "yes"),
        ),
        (
            "INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("bad-sex", "project-1", "melanoma", 1, "X", "miraclib", "yes"),
        ),
        (
            "INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("bad-response", "project-1", "melanoma", 1, "M", "miraclib", "maybe"),
        ),
        (
            "INSERT INTO samples VALUES (?, ?, ?, ?)",
            ("bad-time", "subject-1", "PBMC", -1),
        ),
        (
            "INSERT INTO cell_counts VALUES (?, ?, ?)",
            ("sample-1", 1, -1),
        ),
    ],
)
def test_check_constraints_reject_invalid_rows(
    schema_connection: sqlite3.Connection,
    statement: str,
    parameters: tuple[object, ...],
) -> None:
    _insert_parent_rows(schema_connection)
    with pytest.raises(sqlite3.IntegrityError):
        schema_connection.execute(statement, parameters)


def test_sample_subject_type_time_is_unique(schema_connection: sqlite3.Connection) -> None:
    _insert_parent_rows(schema_connection)
    with pytest.raises(sqlite3.IntegrityError):
        schema_connection.execute("INSERT INTO samples VALUES ('sample-2', 'subject-1', 'PBMC', 0)")


def test_count_foreign_keys_reject_orphans(schema_connection: sqlite3.Connection) -> None:
    _insert_parent_rows(schema_connection)
    with pytest.raises(sqlite3.IntegrityError):
        schema_connection.execute("INSERT INTO cell_counts VALUES ('missing', 1, 1)")
    with pytest.raises(sqlite3.IntegrityError):
        schema_connection.execute("INSERT INTO cell_counts VALUES ('sample-1', 999, 1)")
