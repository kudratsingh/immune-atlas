"""Create configured SQLite connections and manage bulk-load pragmas."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a row-oriented SQLite connection with foreign keys enforced."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def bulk_load_mode(connection: sqlite3.Connection) -> Iterator[None]:
    """Disable journaling for one fresh bulk load, then restore DELETE mode."""
    if connection.in_transaction:
        raise RuntimeError("bulk load mode must begin outside a transaction")
    connection.execute("PRAGMA journal_mode = OFF")
    try:
        yield
    finally:
        connection.rollback()
        connection.execute("PRAGMA journal_mode = DELETE")
