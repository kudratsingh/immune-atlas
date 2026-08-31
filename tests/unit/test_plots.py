from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd
import pytest

from immune_atlas import config
from immune_atlas.analysis.plots import PALETTE, response_boxplots


def _frequencies() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"population": population, "response": response, "percentage": value}
            for population_index, population in enumerate(config.POPULATIONS)
            for response, offset in (("yes", 1.0), ("no", -1.0))
            for value in (
                20.0 + population_index + offset,
                20.5 + population_index + offset,
                21.0 + population_index + offset,
                21.5 + population_index + offset,
            )
        ]
    )


def test_response_boxplots_produce_stable_population_and_combined_pngs(tmp_path: Path) -> None:
    first = response_boxplots(_frequencies(), tmp_path / "first")
    second = response_boxplots(_frequencies().sample(frac=1.0, random_state=8), tmp_path / "second")

    expected_names = [
        *(f"response_boxplot_{population}.png" for population in config.POPULATIONS),
        "response_boxplots.png",
    ]
    assert [path.name for path in first] == expected_names
    assert [path.name for path in second] == expected_names
    assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in first)
    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
    assert mpimg.imread(first[0]).shape[:2] == (576, 768)


def test_palette_matches_fixed_dashboard_response_colours() -> None:
    assert PALETTE["responder"] == "#0891B2"
    assert PALETTE["non_responder"] == "#B45309"
    assert [PALETTE[f"population_{index}"] for index in range(1, 6)] == [
        "#1E3A8A",
        "#2F55B3",
        "#4F7BD9",
        "#86A8EA",
        "#BFD3F3",
    ]


def test_response_boxplots_reject_invalid_frames(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        response_boxplots(_frequencies().drop(columns="percentage"), tmp_path)
    with pytest.raises(ValueError, match="no responder"):
        response_boxplots(_frequencies().assign(response="unknown"), tmp_path)
    with pytest.raises(ValueError, match="finite numbers"):
        response_boxplots(_frequencies().assign(percentage="bad"), tmp_path)
    with pytest.raises(ValueError, match="missing configured populations"):
        response_boxplots(
            _frequencies().loc[_frequencies()["population"] != config.POPULATIONS[-1]],
            tmp_path,
        )
