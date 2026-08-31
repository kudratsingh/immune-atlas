"""Define shared analysis constants and resolve repository paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

POPULATIONS: Final = ("b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte")
POPULATION_DISPLAY_NAMES: Final = MappingProxyType(
    {
        "b_cell": "B cells",
        "cd8_t_cell": "CD8 T cells",
        "cd4_t_cell": "CD4 T cells",
        "nk_cell": "NK cells",
        "monocyte": "Monocytes",
    }
)
FREQUENCY_COLUMNS: Final = ("sample", "total_count", "population", "count", "percentage")
RESPONSE_COMPARISON_COLUMNS: Final = (
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
SCHEMA_VERSION: Final = "1.0"
BASELINE_TIME: Final = 0
ALPHA: Final = 0.05


@dataclass(frozen=True, slots=True)
class CohortFilter:
    """Describe a condition, treatment, sample type, and optional time point."""

    condition: str
    treatment: str
    sample_type: str
    time: int | None = None

    def __post_init__(self) -> None:
        """Reject filters that cannot identify a valid cohort."""
        for field_name in ("condition", "treatment", "sample_type"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.time is not None and self.time < 0:
            raise ValueError("time must be non-negative")

    def to_dict(self) -> dict[str, str | int]:
        """Return the bundle representation, omitting an unspecified time point."""
        values: dict[str, str | int] = {
            "condition": self.condition,
            "treatment": self.treatment,
            "sample_type": self.sample_type,
        }
        if self.time is not None:
            values["time"] = self.time
        return values


RESPONSE_COHORT: Final = CohortFilter(
    condition="melanoma", treatment="miraclib", sample_type="PBMC"
)

REPO_ROOT: Final = Path(__file__).resolve().parents[1]


def _path_from_env(variable: str, default: Path) -> Path:
    raw_value = os.getenv(variable)
    path = Path(raw_value).expanduser() if raw_value else default
    return path.resolve()


CSV_PATH: Final = _path_from_env("IMMUNE_ATLAS_CSV", REPO_ROOT / "data" / "cell-count.csv")
DB_PATH: Final = _path_from_env("IMMUNE_ATLAS_DB", REPO_ROOT / "cell_counts.db")
OUTPUTS_DIR: Final = _path_from_env("IMMUNE_ATLAS_OUTPUTS", REPO_ROOT / "outputs")
PLOTS_DIR: Final = OUTPUTS_DIR / "plots"
CONTRACT_PATH: Final = REPO_ROOT / "contracts" / "dashboard-bundle.schema.json"
FIXTURE_BUNDLE_PATH: Final = REPO_ROOT / "contracts" / "fixtures" / "bundle.small.json"
DASHBOARD_BUNDLE_PATH: Final = REPO_ROOT / "dashboard" / "public" / "data" / "bundle.json"
