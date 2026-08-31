"""Render deterministic responder box plots with the dashboard colour system."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from immune_atlas import config

PALETTE: Final = {
    "paper": "#F4F7FA",
    "panel": "#FFFFFF",
    "ink": "#14213D",
    "ink_muted": "#5B6B84",
    "rule": "#DDE5EE",
    "responder": "#0891B2",
    "non_responder": "#B45309",
    "population_1": "#1E3A8A",
    "population_2": "#2F55B3",
    "population_3": "#4F7BD9",
    "population_4": "#86A8EA",
    "population_5": "#BFD3F3",
    "focus": "#1D4ED8",
}
_SEED = 20260830
_DPI = 120


def _validate(frequencies: pd.DataFrame) -> pd.DataFrame:
    required = ("population", "response", "percentage")
    missing = [column for column in required if column not in frequencies.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    frame = frequencies.loc[frequencies["response"].isin(("yes", "no")), required].copy()
    if frame.empty:
        raise ValueError("no responder or non-responder values to plot")
    frame["percentage"] = pd.to_numeric(frame["percentage"], errors="coerce")
    if (
        frame["percentage"].isna().any()
        or not np.isfinite(frame["percentage"].to_numpy(dtype=float)).all()
    ):
        raise ValueError("percentage values must be finite numbers")
    missing_populations = [
        population
        for population in config.POPULATIONS
        if population not in set(frame["population"])
    ]
    if missing_populations:
        raise ValueError(f"missing configured populations: {', '.join(missing_populations)}")
    return frame


def _draw_population(
    ax: Axes, frame: pd.DataFrame, population: str, rng: np.random.Generator
) -> None:
    values = [
        np.sort(
            frame.loc[
                (frame["population"] == population) & (frame["response"] == response),
                "percentage",
            ].to_numpy(dtype=float)
        )
        for response in ("yes", "no")
    ]
    boxes = ax.boxplot(values, positions=[1, 2], widths=0.55, patch_artist=True, showfliers=False)
    for patch, colour in zip(
        boxes["boxes"], (PALETTE["responder"], PALETTE["non_responder"]), strict=True
    ):
        patch.set(facecolor=colour, edgecolor=PALETTE["ink"], alpha=0.28, linewidth=1.0)
    for median in boxes["medians"]:
        median.set(color=PALETTE["ink"], linewidth=1.6)
    for line in (*boxes["whiskers"], *boxes["caps"]):
        line.set(color=PALETTE["ink_muted"], linewidth=1.0)
    for position, group, colour in zip(
        (1, 2), values, (PALETTE["responder"], PALETTE["non_responder"]), strict=True
    ):
        jitter = rng.uniform(-0.12, 0.12, size=len(group))
        ax.scatter(position + jitter, group, s=11, alpha=0.42, color=colour, edgecolors="none")
    display_name = config.POPULATION_DISPLAY_NAMES[population]
    ax.set_title(display_name, color=PALETTE["ink"], fontsize=11, loc="left")
    ax.set_xticks(
        [1, 2],
        labels=[f"Responders\n(n={len(values[0])})", f"Non-responders\n(n={len(values[1])})"],
    )
    ax.set_ylabel("Relative frequency (%)")
    ax.grid(axis="y", color=PALETTE["ink_muted"], alpha=0.2, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(PALETTE["rule"])
    ax.tick_params(colors=PALETTE["ink_muted"], labelsize=9)
    ax.set_facecolor(PALETTE["panel"])


def _save(fig: Figure, path: Path) -> None:
    fig.savefig(
        path,
        dpi=_DPI,
        facecolor=PALETTE["panel"],
        bbox_inches=None,
        metadata={"Software": None},
    )
    plt.close(fig)


def response_boxplots(frequencies: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Write one responder box plot per population and one combined figure.

    Input columns are `population, response, percentage`; response values outside
    `yes, no` are ignored. Output is a deterministic ordered list of paths named
    `response_boxplot_<population>.png` for each configured population followed by
    `response_boxplots.png`. Rendering uses Agg, fixed sizes and DPI, a seeded jitter,
    and PNG metadata without a software field.
    """
    frame = _validate(frequencies)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    rng = np.random.default_rng(_SEED)
    for population in config.POPULATIONS:
        fig, ax = plt.subplots(figsize=(6.4, 4.8), layout="constrained")
        _draw_population(ax, frame, population, rng)
        path = out_dir / f"response_boxplot_{population}.png"
        _save(fig, path)
        paths.append(path)

    fig, axes = plt.subplots(2, 3, figsize=(12.0, 7.6), layout="constrained")
    for ax, population in zip(axes.flat, config.POPULATIONS, strict=False):
        _draw_population(ax, frame, population, rng)
    axes.flat[-1].set_visible(False)
    combined = out_dir / "response_boxplots.png"
    _save(fig, combined)
    paths.append(combined)
    return paths
