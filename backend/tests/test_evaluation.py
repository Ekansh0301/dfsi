"""The evaluation compares the required models and is reproducible (Issue T6)."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_synthetic import run_seed  # noqa: E402

METRICS = {"auc", "accuracy", "log_loss", "rmse"}
MODELS = {"Global average", "Per-question accuracy", "Learner's running accuracy", "BKT (hand-set parameters)", "BKT (fitted)"}
DIAGNOSIS = {"gap_f1", "recommendation_is_true_blocker", "hidden_prereq_blocker_hit", "missed_gap_rate", "false_alarm_rate"}


@pytest.fixture(scope="module")
def run():
    return run_seed(seed=3, n_learners=120)


def test_every_baseline_is_scored_on_every_metric(run):
    assert set(run["ladder"]) == MODELS
    for name, scores in run["ladder"].items():
        assert METRICS <= set(scores), name
        assert 0 <= scores["auc"] <= 1 and 0 <= scores["accuracy"] <= 1 and scores["log_loss"] > 0 and scores["rmse"] > 0


def test_global_average_is_the_chance_level_baseline(run):
    assert run["ladder"]["Global average"]["auc"] == pytest.approx(0.5)


def test_diagnosis_is_scored_for_every_method_and_parameter_set(run):
    for tag in ("fitted", "hand_set"):
        methods = {k: v for k, v in run["diagnosis"][tag].items() if not k.startswith("_")}
        assert len(methods) == 3
        for name, scores in methods.items():
            assert DIAGNOSIS <= set(scores), (tag, name)
        assert {"auc", "brier", "mean_abs_error"} <= set(run["diagnosis"][tag]["_mastery_estimates"])


def test_the_same_seed_gives_the_same_report(run):
    again = run_seed(seed=3, n_learners=120)
    assert json.dumps(again, sort_keys=True) == json.dumps(run, sort_keys=True)


def test_committed_report_has_the_required_metrics():
    text = (ROOT / "results" / "synthetic_results.md").read_text(encoding="utf8")
    for needle in ("AUC", "Accuracy", "Log loss", "RMSE", "Global average", "Per-question accuracy", "running accuracy", "BKT (fitted)", "prerequisite walk", "Gap F1"):
        assert needle in text, needle
    runs = json.loads((ROOT / "results" / "synthetic_results.json").read_text(encoding="utf8"))
    assert len(runs) == 5 and [r["seed"] for r in runs] == list(range(5))
