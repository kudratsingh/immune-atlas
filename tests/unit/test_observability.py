"""Tests for logging, stage timing, and run-report serialization."""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path

import jsonschema
import pytest

from immune_atlas import config
from immune_atlas.observability import Metrics, Timer, configure_logging, get_logger

SOURCE_SHA256 = "0" * 64
LIBRARY_VERSIONS = {
    "pandas": "3.0.5",
    "numpy": "2.4.6",
    "scipy": "1.17.1",
    "matplotlib": "3.11.1",
    "jsonschema": "4.26.0",
}


@pytest.fixture(autouse=True)
def reset_immune_atlas_logger() -> None:
    logger = logging.getLogger("immune_atlas")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    logger.propagate = True
    yield
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    logger.propagate = True


def test_plain_logging_is_idempotent_and_respects_level() -> None:
    stream = io.StringIO()
    configure_logging("WARNING", json_format=False, stream=stream)
    configure_logging("WARNING", json_format=False, stream=stream)
    logger = get_logger("immune_atlas.test")
    logger.info("hidden")
    logger.warning("rows=%d", 12)
    assert stream.getvalue() == "WARNING immune_atlas.test rows=12\n"
    assert len(logging.getLogger("immune_atlas").handlers) == 1


def test_json_logging_uses_environment_default(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = io.StringIO()
    monkeypatch.setenv("IMMUNE_ATLAS_LOG_JSON", "yes")
    configure_logging(stream=stream)
    get_logger("immune_atlas.test").info("loaded %d rows", 5)
    payload = json.loads(stream.getvalue())
    assert payload["level"] == "INFO"
    assert payload["logger"] == "immune_atlas.test"
    assert payload["message"] == "loaded 5 rows"
    assert payload["timestamp"].endswith("+00:00")


def test_explicit_plain_logging_overrides_json_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = io.StringIO()
    monkeypatch.setenv("IMMUNE_ATLAS_LOG_JSON", "1")
    configure_logging(json_format=False, stream=stream)
    get_logger("immune_atlas.test").error("plain")
    assert stream.getvalue() == "ERROR immune_atlas.test plain\n"


def test_json_logging_includes_exception() -> None:
    stream = io.StringIO()
    configure_logging(json_format=True, stream=stream)
    try:
        raise RuntimeError("broken stage")
    except RuntimeError:
        get_logger("immune_atlas.test").exception("pipeline failed")
    payload = json.loads(stream.getvalue())
    assert payload["message"] == "pipeline failed"
    assert "RuntimeError: broken stage" in payload["exception"]


def test_metrics_serialization_is_stable_and_copies_inputs(tmp_path: Path) -> None:
    versions = dict(LIBRARY_VERSIONS)
    metrics = Metrics(
        source_sha256=SOURCE_SHA256,
        pipeline_version="9.9.9",
        library_versions=versions,
    )
    versions["pandas"] = "changed"
    metrics.record_stage("load_database", seconds=0.125, rows_in=2, rows_out=10)
    metrics.add_warning("small synthetic cohort")

    report = metrics.to_dict()
    assert report["source_sha256"] == SOURCE_SHA256
    assert report["pipeline_version"] == "9.9.9"
    assert report["library_versions"] == {
        "jsonschema": "4.26.0",
        "matplotlib": "3.11.1",
        "numpy": "2.4.6",
        "pandas": "3.0.5",
        "scipy": "1.17.1",
    }
    assert report["stages"] == [
        {"name": "load_database", "seconds": 0.125, "rows_in": 2, "rows_out": 10}
    ]
    assert report["warnings"] == ["small synthetic cohort"]

    output = tmp_path / "nested" / "pipeline_run.json"
    metrics.write(output)
    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert output.read_bytes().endswith(b"\n")


def test_metrics_report_matches_the_dashboard_contract() -> None:
    schema = json.loads(config.CONTRACT_PATH.read_text(encoding="utf-8"))
    fixture = json.loads(config.FIXTURE_BUNDLE_PATH.read_text(encoding="utf-8"))
    metrics = Metrics(source_sha256=SOURCE_SHA256)
    metrics.record_stage("load_database", seconds=0.1, rows_in=2, rows_out=10)
    fixture["run"] = metrics.to_dict()

    jsonschema.validate(fixture, schema, format_checker=jsonschema.FormatChecker())


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"name": "", "seconds": 0.0}, "stage name"),
        ({"name": "stage", "seconds": -0.1}, "seconds"),
        ({"name": "stage", "seconds": 0.1, "rows_in": -1}, "rows_in"),
        ({"name": "stage", "seconds": 0.1, "rows_out": -1}, "rows_out"),
    ],
)
def test_metrics_reject_invalid_stage_values(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Metrics(source_sha256=SOURCE_SHA256).record_stage(  # type: ignore[arg-type]
            **kwargs
        )


def test_metrics_reject_duplicate_stages_and_empty_warnings() -> None:
    metrics = Metrics(source_sha256=SOURCE_SHA256)
    metrics.record_stage("load", seconds=0.1)
    with pytest.raises(ValueError, match="already recorded"):
        metrics.record_stage("load", seconds=0.2)
    with pytest.raises(ValueError, match="warning"):
        metrics.add_warning(" ")


@pytest.mark.parametrize(
    "versions",
    [
        {"pandas": "3.0.5"},
        {**LIBRARY_VERSIONS, "unknown": "1.0"},
    ],
)
def test_metrics_reject_library_version_key_mismatches(versions: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="library_versions keys mismatch"):
        Metrics(source_sha256=SOURCE_SHA256, library_versions=versions)


def test_timer_records_elapsed_time_and_rows() -> None:
    stream = io.StringIO()
    configure_logging(stream=stream)
    ticks = iter((10.0, 10.25))
    metrics = Metrics(source_sha256=SOURCE_SHA256)
    with Timer("frequencies", metrics, rows_in=2, clock=lambda: next(ticks)) as timer:
        timer.set_rows_out(10)
    assert timer.elapsed == 0.25
    assert metrics.to_dict()["stages"] == [
        {"name": "frequencies", "seconds": 0.25, "rows_in": 2, "rows_out": 10}
    ]
    assert "stage_started name=frequencies" in stream.getvalue()
    assert "stage_completed name=frequencies seconds=0.250000 rows_in=2 rows_out=10" in (
        stream.getvalue()
    )


def test_timer_records_failed_stage_and_propagates_exception() -> None:
    stream = io.StringIO()
    configure_logging(stream=stream)
    ticks = iter((3.0, 2.0))
    metrics = Metrics(source_sha256=SOURCE_SHA256)
    with (
        pytest.raises(RuntimeError, match="failure"),
        Timer("analysis", metrics, clock=lambda: next(ticks)),
    ):
        raise RuntimeError("failure")
    assert metrics.stages[0].seconds == 0.0
    assert "stage_started name=analysis" in stream.getvalue()
    assert "stage_failed name=analysis seconds=0.000000" in stream.getvalue()
    assert "RuntimeError: failure" in stream.getvalue()


def test_timer_rejects_invalid_rows_and_reentry() -> None:
    metrics = Metrics(source_sha256=SOURCE_SHA256)
    with pytest.raises(ValueError, match="rows_in"):
        Timer("load", metrics, rows_in=-1)
    timer = Timer("load", metrics, clock=lambda: 1.0)
    timer.__enter__()
    with pytest.raises(RuntimeError, match="more than once"):
        timer.__enter__()
    with pytest.raises(ValueError, match="rows_out"):
        timer.set_rows_out(-1)
    timer.__exit__(None, None, None)


def test_timer_cannot_exit_before_entry() -> None:
    with pytest.raises(RuntimeError, match="not entered"):
        Timer("load", Metrics(source_sha256=SOURCE_SHA256)).__exit__(None, None, None)


@pytest.mark.parametrize("checksum", ["", "abc", "G" * 64, "0" * 63])
def test_metrics_reject_invalid_source_checksum(checksum: str) -> None:
    with pytest.raises(ValueError, match="source_sha256"):
        Metrics(source_sha256=checksum)
