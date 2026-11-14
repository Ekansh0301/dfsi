"""The accuracy engine used as a comparison baseline (scripts/accuracy_baseline.py)."""

import json
from pathlib import Path

import pytest

from circuit_coach.accuracy_engine import AccuracyEngine
from circuit_coach.engine import Event, LearnerState

ROOT = Path(__file__).resolve().parents[1]


def ev(correct, *tags, unsure=False, score=None):
    return Event(tuple(tags) or ("ohm",), correct, unsure, score=score)


def test_mastery_is_smoothed_accuracy():
    e = AccuracyEngine()
    assert e.trace(LearnerState(), [ev(True)]).mastery["ohm"] == pytest.approx(2 / 3)
    assert e.trace(LearnerState(), [ev(False)]).mastery["ohm"] == pytest.approx(1 / 3)
    assert e.trace(LearnerState(), [ev(True), ev(False)]).mastery["ohm"] == pytest.approx(0.5)


def test_unsure_counts_as_wrong_and_partial_credit_counts_in_part():
    e = AccuracyEngine()
    assert e.trace(LearnerState(), [ev(True, unsure=True)]).mastery["ohm"] == pytest.approx(1 / 3)
    assert e.trace(LearnerState(), [ev(False, score=0.5)]).mastery["ohm"] == pytest.approx(0.5)


def test_tracing_in_two_steps_equals_tracing_at_once():
    e = AccuracyEngine()
    events = [ev(True), ev(False), ev(False, "diagrams", "symbols"), ev(True, "diagrams")]
    at_once = e.trace(LearnerState(), events)
    in_steps = e.trace(e.trace(LearnerState(), events[:2]), events[2:])
    assert in_steps.observations == at_once.observations
    assert in_steps.mastery == pytest.approx(at_once.mastery)


def test_it_uses_the_same_walk_and_threshold():
    e = AccuracyEngine()
    st = e.trace(LearnerState(), [ev(False, "symbols"), ev(False, "diagrams"), ev(False, "diagrams")])
    rec = e.recommend(st, ["diagrams"])
    assert rec["observed_concept_id"] == "diagrams" and rec["concept_id"] == "symbols"


def test_the_committed_report_covers_both_simulators():
    data = json.loads((ROOT / "results" / "accuracy_baseline.json").read_text(encoding="utf8"))
    assert set(data) == {"sprint2", "barabari"} and all(len(v) == 5 for v in data.values())
    report = (ROOT / "results" / "accuracy_baseline.md").read_text(encoding="utf8")
    assert "Accuracy + prerequisite walk" in report and "BKT baseline + prerequisite walk" in report
