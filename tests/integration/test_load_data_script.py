from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest


def _run_script(repo: Path) -> tuple[subprocess.CompletedProcess[str], float]:
    environment = os.environ.copy()
    for variable in ("IMMUNE_ATLAS_CSV", "IMMUNE_ATLAS_DB", "IMMUNE_ATLAS_OUTPUTS"):
        environment.pop(variable, None)
    started_at = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "load_data.py"],
        cwd=repo,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    return completed, time.perf_counter() - started_at


@pytest.mark.integration
def test_no_argument_script_creates_database_and_is_idempotent(temp_repo: Path) -> None:
    db_path = temp_repo / "cell_counts.db"
    db_path.unlink(missing_ok=True)

    first, first_seconds = _run_script(temp_repo)
    assert first.returncode == 0, first.stderr
    assert first.stdout.count("\n") == 1
    assert "Loaded 10,500 samples, 3,500 subjects, and 52,500 cell counts" in first.stdout
    assert db_path.is_file()
    first_bytes = db_path.read_bytes()

    second, second_seconds = _run_script(temp_repo)
    assert second.returncode == 0, second.stderr
    assert db_path.read_bytes() == first_bytes
    assert max(first_seconds, second_seconds) < 5

    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM samples").fetchone()[0] == 10_500
        assert connection.execute("SELECT COUNT(*) FROM subjects").fetchone()[0] == 3_500
        assert connection.execute("SELECT COUNT(*) FROM cell_counts").fetchone()[0] == 52_500


def test_script_exits_nonzero_when_input_is_missing(temp_repo: Path) -> None:
    (temp_repo / "data" / "cell-count.csv").unlink()
    completed, _ = _run_script(temp_repo)
    assert completed.returncode == 1
    assert "load failed: input CSV not found" in completed.stderr
