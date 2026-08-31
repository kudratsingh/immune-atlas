"""Create the repository-root SQLite database from the bundled source CSV."""

from __future__ import annotations

import sys

from immune_atlas.config import CSV_PATH, DB_PATH
from immune_atlas.db.loader import run
from immune_atlas.observability import configure_logging


def main() -> int:
    """Load the default CSV and print a one-line row-count summary."""
    configure_logging()
    try:
        report = run(CSV_PATH, DB_PATH)
    except Exception as error:
        print(f"load failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Loaded {report.samples:,} samples, {report.subjects:,} subjects, "
        f"and {report.counts:,} cell counts into {DB_PATH.name}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
