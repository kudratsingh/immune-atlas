from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from immune_atlas.observability import Metrics
from immune_atlas.pipeline import PipelineContext, run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(base: Path) -> Path:
    csv_path = REPO_ROOT / "data" / "cell-count.csv"
    context = PipelineContext(
        csv_path=csv_path,
        db_path=base / "cell_counts.db",
        outputs_dir=base / "outputs",
        plots_dir=base / "outputs" / "plots",
        bundle_path=base / "bundle.json",
        contract_path=REPO_ROOT / "contracts" / "dashboard-bundle.schema.json",
        metrics=Metrics(source_sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest()),
    )
    run_pipeline(context)
    context.close()
    return base


def _digests(base: Path) -> dict[str, str]:
    return {
        str(path.relative_to(base)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(base.rglob("*"))
        if path.is_file()
    }


@pytest.mark.integration
def test_two_runs_produce_identical_bytes_except_the_run_report(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    first = _digests(_run(tmp_path_factory.mktemp("determinism-a")))
    second = _digests(_run(tmp_path_factory.mktemp("determinism-b")))
    assert first.keys() == second.keys()
    differing = {name for name in first if first[name] != second[name]}
    # Stage timings are wall-clock, so the run report legitimately differs; the
    # bundle embeds the same stages with seconds zeroed and must not.
    assert differing <= {"outputs/pipeline_run.json"}
