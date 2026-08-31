"""Tests for shared constants, cohort filters, paths, and bundle contract."""

from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import jsonschema
import pandas as pd
import pytest

from immune_atlas import config


def test_analysis_constants_match_the_fixed_contract() -> None:
    assert config.POPULATIONS == (
        "b_cell",
        "cd8_t_cell",
        "cd4_t_cell",
        "nk_cell",
        "monocyte",
    )
    assert tuple(config.POPULATION_DISPLAY_NAMES) == config.POPULATIONS
    assert config.POPULATION_DISPLAY_NAMES["cd4_t_cell"] == "CD4 T cells"
    assert config.FREQUENCY_COLUMNS == (
        "sample",
        "total_count",
        "population",
        "count",
        "percentage",
    )
    assert config.RESPONSE_COMPARISON_COLUMNS == (
        "population",
        "n_yes",
        "n_no",
        "mean_yes",
        "mean_no",
        "sd_yes",
        "sd_no",
        "median_yes",
        "median_no",
        "iqr_low_yes",
        "iqr_high_yes",
        "iqr_low_no",
        "iqr_high_no",
        "u_statistic",
        "p_value",
        "q_value",
        "effect_size",
        "welch_p",
        "significant_raw",
        "significant_adjusted",
    )
    assert config.BASELINE_TIME == 0
    assert config.ALPHA == 0.05
    assert config.SCHEMA_VERSION == "1.0"


def test_population_display_names_are_immutable() -> None:
    with pytest.raises(TypeError):
        config.POPULATION_DISPLAY_NAMES["b_cell"] = "changed"  # type: ignore[index]


def test_cohort_filter_is_frozen_and_serializes_optional_time() -> None:
    assert config.RESPONSE_COHORT.to_dict() == {
        "condition": "melanoma",
        "treatment": "miraclib",
        "sample_type": "PBMC",
    }
    baseline = config.CohortFilter("melanoma", "miraclib", "PBMC", time=0)
    assert baseline.to_dict()["time"] == 0
    with pytest.raises(FrozenInstanceError):
        baseline.time = 7  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"condition": "", "treatment": "miraclib", "sample_type": "PBMC"}, "condition"),
        ({"condition": "melanoma", "treatment": " ", "sample_type": "PBMC"}, "treatment"),
        ({"condition": "melanoma", "treatment": "miraclib", "sample_type": ""}, "sample_type"),
        (
            {"condition": "melanoma", "treatment": "miraclib", "sample_type": "PBMC", "time": -1},
            "time",
        ),
    ],
)
def test_cohort_filter_rejects_invalid_values(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        config.CohortFilter(**kwargs)  # type: ignore[arg-type]


def test_default_paths_are_anchored_to_the_repository() -> None:
    assert config.CSV_PATH == config.REPO_ROOT / "data" / "cell-count.csv"
    assert config.DB_PATH == config.REPO_ROOT / "cell_counts.db"
    assert config.OUTPUTS_DIR == config.REPO_ROOT / "outputs"
    assert config.PLOTS_DIR == config.OUTPUTS_DIR / "plots"
    assert config.CONTRACT_PATH.is_file()
    assert config.FIXTURE_BUNDLE_PATH.is_file()


def test_path_environment_overrides_support_relative_and_absolute_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with monkeypatch.context() as patch:
        patch.chdir(tmp_path)
        patch.setenv("IMMUNE_ATLAS_CSV", "input.csv")
        patch.setenv("IMMUNE_ATLAS_DB", str(tmp_path / "database.sqlite"))
        patch.setenv("IMMUNE_ATLAS_OUTPUTS", "generated")
        reloaded = importlib.reload(config)
        assert tmp_path / "input.csv" == reloaded.CSV_PATH
        assert tmp_path / "database.sqlite" == reloaded.DB_PATH
        assert tmp_path / "generated" == reloaded.OUTPUTS_DIR
    importlib.reload(config)


def test_dashboard_fixture_validates_against_the_contract() -> None:
    schema = json.loads(config.CONTRACT_PATH.read_text(encoding="utf-8"))
    fixture = json.loads(config.FIXTURE_BUNDLE_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(fixture, schema, format_checker=jsonschema.FormatChecker())
    assert schema["properties"]["schema_version"]["const"] == config.SCHEMA_VERSION
    assert tuple(schema["$defs"]["Population"]["enum"]) == config.POPULATIONS


def test_contract_closes_every_structured_object() -> None:
    schema = json.loads(config.CONTRACT_PATH.read_text(encoding="utf-8"))
    open_objects: list[str] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object" and value.get("additionalProperties") is not False:
                open_objects.append(path)
            for key, child in value.items():
                visit(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(schema, "$")
    assert open_objects == []


def test_shared_tabular_fixtures_have_expected_shapes(
    synthetic_wide_frame: pd.DataFrame,
    synthetic_long_frame: pd.DataFrame,
    temp_repo: Path,
    real_csv_path: Path,
) -> None:
    assert synthetic_wide_frame.shape == (2, 15)
    assert synthetic_long_frame.shape == (10, 12)
    assert (temp_repo / "CLAUDE.md").is_file()
    assert real_csv_path.is_file()
