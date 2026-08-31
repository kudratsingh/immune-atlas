"""Provide structured pipeline logging and deterministic run metrics."""

from __future__ import annotations

import json
import logging
import os
import platform
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from types import TracebackType
from typing import Literal, TextIO

from immune_atlas import __version__

_LOGGER_NAMESPACE = "immune_atlas"
_HANDLER_MARKER = "_immune_atlas_handler"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_CORE_LIBRARIES = frozenset({"pandas", "numpy", "scipy", "matplotlib", "jsonschema"})


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True)


def _json_logging_enabled() -> bool:
    return os.getenv("IMMUNE_ATLAS_LOG_JSON", "").strip().lower() in _TRUE_VALUES


def _installed_library_versions() -> dict[str, str]:
    return {name: version(name) for name in sorted(_CORE_LIBRARIES)}


def configure_logging(
    level: int | str = logging.INFO,
    json_format: bool | None = None,
    *,
    stream: TextIO | None = None,
) -> None:
    """Configure the Immune Atlas logger without adding duplicate handlers."""
    logger = logging.getLogger(_LOGGER_NAMESPACE)
    logger.setLevel(level)
    logger.propagate = False

    handler = next(
        (candidate for candidate in logger.handlers if getattr(candidate, _HANDLER_MARKER, False)),
        None,
    )
    if handler is None:
        handler = logging.StreamHandler(stream)
        setattr(handler, _HANDLER_MARKER, True)
        logger.addHandler(handler)
    elif stream is not None and isinstance(handler, logging.StreamHandler):
        handler.setStream(stream)

    handler.setLevel(level)
    use_json = _json_logging_enabled() if json_format is None else json_format
    formatter: logging.Formatter
    if use_json:
        formatter = _JsonFormatter()
    else:
        formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    """Return a standard-library logger for a module."""
    return logging.getLogger(name)


@dataclass(frozen=True, slots=True)
class StageMetrics:
    """Store duration and row gauges for one pipeline stage."""

    name: str
    seconds: float
    rows_in: int | None = None
    rows_out: int | None = None


class Metrics:
    """Collect ordered stage metrics and warnings for one pipeline run."""

    def __init__(
        self,
        *,
        source_sha256: str,
        pipeline_version: str = __version__,
        library_versions: Mapping[str, str] | None = None,
    ) -> None:
        """Create an empty run report with stable version metadata."""
        if re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None:
            raise ValueError("source_sha256 must be 64 lowercase hexadecimal characters")
        resolved_versions = (
            dict(library_versions)
            if library_versions is not None
            else _installed_library_versions()
        )
        if set(resolved_versions) != _CORE_LIBRARIES:
            missing = sorted(_CORE_LIBRARIES - set(resolved_versions))
            extra = sorted(set(resolved_versions) - _CORE_LIBRARIES)
            raise ValueError(f"library_versions keys mismatch: missing={missing}, extra={extra}")
        self.source_sha256 = source_sha256
        self.pipeline_version = pipeline_version
        self.python_version = platform.python_version()
        self.library_versions = resolved_versions
        self.stages: list[StageMetrics] = []
        self.warnings: list[str] = []

    def record_stage(
        self,
        name: str,
        *,
        seconds: float,
        rows_in: int | None = None,
        rows_out: int | None = None,
    ) -> None:
        """Append timing and row gauges for a uniquely named stage."""
        if not name.strip():
            raise ValueError("stage name must not be empty")
        if seconds < 0:
            raise ValueError("stage seconds must be non-negative")
        for label, value in (("rows_in", rows_in), ("rows_out", rows_out)):
            if value is not None and value < 0:
                raise ValueError(f"{label} must be non-negative")
        if any(stage.name == name for stage in self.stages):
            raise ValueError(f"stage already recorded: {name}")
        self.stages.append(
            StageMetrics(name=name, seconds=seconds, rows_in=rows_in, rows_out=rows_out)
        )

    def add_warning(self, message: str) -> None:
        """Append a non-empty pipeline warning in encounter order."""
        if not message.strip():
            raise ValueError("warning must not be empty")
        self.warnings.append(message)

    def to_dict(self) -> dict[str, object]:
        """Return the JSON-serializable dashboard run-report shape."""
        return {
            "source_sha256": self.source_sha256,
            "pipeline_version": self.pipeline_version,
            "python_version": self.python_version,
            "library_versions": dict(sorted(self.library_versions.items())),
            "stages": [asdict(stage) for stage in self.stages],
            "warnings": list(self.warnings),
        }

    def write(self, path: Path) -> None:
        """Write the run report as deterministic, newline-terminated JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"{json.dumps(self.to_dict(), indent=2, sort_keys=True)}\n",
            encoding="utf-8",
        )


class Timer:
    """Measure one pipeline stage and record it in a Metrics collector."""

    def __init__(
        self,
        name: str,
        metrics: Metrics,
        *,
        rows_in: int | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """Prepare a timer; timing begins when its context is entered."""
        if rows_in is not None and rows_in < 0:
            raise ValueError("rows_in must be non-negative")
        self.name = name
        self.metrics = metrics
        self.rows_in = rows_in
        self.rows_out: int | None = None
        self.elapsed: float | None = None
        self._clock = clock or time.perf_counter
        self._started_at: float | None = None
        self._logger = get_logger(__name__)

    def set_rows_out(self, rows_out: int | None) -> None:
        """Set the output-row gauge before the context exits."""
        if rows_out is not None and rows_out < 0:
            raise ValueError("rows_out must be non-negative")
        self.rows_out = rows_out

    def __enter__(self) -> Timer:
        """Start measuring the stage."""
        if self._started_at is not None:
            raise RuntimeError("timer cannot be entered more than once")
        self._started_at = self._clock()
        self._logger.info("stage_started name=%s", self.name)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Stop measuring, record the stage, and propagate any exception."""
        if self._started_at is None:
            raise RuntimeError("timer was not entered")
        self.elapsed = max(0.0, self._clock() - self._started_at)
        self.metrics.record_stage(
            self.name,
            seconds=self.elapsed,
            rows_in=self.rows_in,
            rows_out=self.rows_out,
        )
        if exc_type is None:
            self._logger.info(
                "stage_completed name=%s seconds=%.6f rows_in=%s rows_out=%s",
                self.name,
                self.elapsed,
                self.rows_in,
                self.rows_out,
            )
        else:
            self._logger.error(
                "stage_failed name=%s seconds=%.6f",
                self.name,
                self.elapsed,
                exc_info=exc_value,
            )
        return False
