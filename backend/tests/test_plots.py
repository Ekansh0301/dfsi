"""The evaluation figures (scripts/plot_results.py) can be drawn from the saved results."""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("plot_results", ROOT / "scripts" / "plot_results.py")
plots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plots)

FIGURES = {
    "model_comparison.png": plots.fig_model_comparison,
    "paired_differences.png": plots.fig_paired,
    "improvement_ladder.png": plots.fig_ladder,
    "bkt_vs_accuracy.png": plots.fig_bkt_vs_accuracy,
    "ednet_prediction.png": plots.fig_ednet,
    "robustness.png": plots.fig_robustness,
    "failure_analysis.png": plots.fig_failure,
}


@pytest.mark.parametrize("name", FIGURES)
def test_each_figure_is_drawn_from_the_saved_results(name, tmp_path):
    FIGURES[name](tmp_path)
    assert (tmp_path / name).stat().st_size > 10_000


def test_the_committed_figures_and_the_overview_exist_and_match():
    overview = (ROOT / "results" / "overview.md").read_text(encoding="utf8")
    for name in [*FIGURES, "calibration.png", "test_coverage.png"]:
        assert (ROOT / "results" / name).exists(), name
        assert f"]({name})" in overview, f"{name} is not shown in results/overview.md"
