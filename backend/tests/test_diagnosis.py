"""Gap detection, the prerequisite walk and lesson choice (Issue T3).

States are written out by hand so each test shows exactly which concepts are weak.
"""

import pytest

from circuit_coach.bkt import HAND_SET
from circuit_coach.curriculum import CONCEPTS, CONTENT
from circuit_coach.engine import WEAK, Engine, LearnerState


@pytest.fixture
def e() -> Engine:
    return Engine({c: HAND_SET for c in CONCEPTS})


def state(tried=None, **mastery) -> LearnerState:
    """Every named concept counts as observed once."""
    return LearnerState(dict(mastery), {c: 1 for c in mastery}, tried or {})


# ---- gap threshold ---------------------------------------------------------------------


def test_gap_threshold_is_point_six(e):
    assert WEAK == 0.6
    assert e.recommend(state(diagrams=0.6), ["diagrams"]) is None
    assert e.recommend(state(diagrams=0.599), ["diagrams"])["concept_id"] == "diagrams"


def test_only_assessed_concepts_can_be_the_observed_gap(e):
    s = state(symbols=0.2, wiring=0.9, diagrams=0.9)
    assert e.recommend(s, ["wiring", "diagrams"]) is None


def test_the_most_advanced_weak_concept_is_the_observed_gap(e):
    # symbols (column 2) and diagrams (column 3) are both weak; diagrams is further along.
    s = state(symbols=0.5, wiring=0.9, diagrams=0.4)
    rec = e.recommend(s, ["symbols", "wiring", "diagrams"])
    assert rec["observed_concept_id"] == "diagrams"


def test_between_equally_advanced_gaps_the_weaker_one_is_chosen(e):
    s = state(series_parallel=0.5, diagrams=0.3)
    assert e.recommend(s, ["series_parallel", "diagrams"])["observed_concept_id"] == "diagrams"


# ---- direct gaps -------------------------------------------------------------------------


def test_direct_gap_when_prerequisites_are_strong(e):
    s = state(symbols=0.9, wiring=0.85, diagrams=0.3)
    rec = e.recommend(s, ["symbols", "wiring", "diagrams"])
    assert rec["concept_id"] == "diagrams" and rec["chain"] == ["diagrams"]
    assert rec["strong_concept_id"] == "symbols"
    assert rec["recommended_content_id"] == CONTENT["diagrams"][0]
    assert rec["repeat_gap"] is False


# ---- prerequisite gaps -------------------------------------------------------------------


def test_weak_prerequisite_is_the_root_cause(e):
    s = state(symbols=0.4, wiring=0.9, diagrams=0.3)
    rec = e.recommend(s, ["symbols", "wiring", "diagrams"])
    assert rec["observed_concept_id"] == "diagrams"
    assert rec["chain"] == ["diagrams", "symbols"] and rec["concept_id"] == "symbols"
    assert rec["recommended_content_id"] == CONTENT["symbols"][0]


def test_the_weakest_of_several_weak_prerequisites_is_followed(e):
    s = state(symbols=0.5, wiring=0.3, diagrams=0.2)
    assert e.recommend(s, ["diagrams"])["chain"] == ["diagrams", "wiring"]


def test_the_walk_continues_through_several_levels(e):
    # fault <- diagrams <- symbols <- quantities, all weak, safety strong.
    s = state(safety=0.9, quantities=0.4, symbols=0.4, wiring=0.9, diagrams=0.3, multimeter=0.9, series_parallel=0.9, fault=0.2)
    rec = e.recommend(s, ["fault"])
    assert rec["chain"] == ["fault", "diagrams", "symbols", "quantities"]
    assert rec["concept_id"] == "quantities"


def test_prerequisites_at_or_above_the_threshold_are_not_blamed(e):
    s = state(symbols=0.6, wiring=0.7, diagrams=0.2)
    assert e.recommend(s, ["diagrams"])["chain"] == ["diagrams"]


def test_only_assessed_prerequisites_are_walked(e):
    # symbols has a low mastery value but no observations: there is no evidence it is weak.
    s = LearnerState(mastery={"symbols": 0.1, "diagrams": 0.2}, observations={"diagrams": 3})
    assert e.recommend(s, ["diagrams"])["chain"] == ["diagrams"]


def test_without_the_walk_the_observed_concept_is_recommended():
    e = Engine({c: HAND_SET for c in CONCEPTS}, use_prerequisites=False)
    s = state(symbols=0.2, diagrams=0.2)
    assert e.recommend(s, ["diagrams"])["chain"] == ["diagrams"]


def test_the_diagnostic_text_names_both_concepts_for_a_prerequisite_gap(e):
    rec = e.recommend(state(symbols=0.4, wiring=0.9, diagrams=0.3), ["diagrams"])
    assert "reading circuit diagrams" in rec["diagnostic_text"]["en"]
    assert "circuit symbols" in rec["diagnostic_text"]["en"]


# ---- tried lessons -----------------------------------------------------------------------


@pytest.mark.parametrize("tried, expected", [([], "ct_diag_walk"), (["ct_diag_walk"], "ct_diag_practice"), (["ct_diag_walk", "ct_diag_practice"], "ct_diag_example")])
def test_the_first_untried_lesson_is_chosen(e, tried, expected):
    s = state(tried={"diagrams": tried}, symbols=0.9, wiring=0.9, diagrams=0.3)
    assert e.recommend(s, ["diagrams"])["recommended_content_id"] == expected


def test_lessons_tried_for_another_concept_do_not_count(e):
    s = state(tried={"symbols": ["ct_sym_cards"]}, symbols=0.9, wiring=0.9, diagrams=0.3)
    assert e.recommend(s, ["diagrams"])["recommended_content_id"] == "ct_diag_walk"


def test_tried_lessons_apply_to_the_root_cause(e):
    s = state(tried={"symbols": ["ct_sym_cards"]}, symbols=0.3, wiring=0.9, diagrams=0.3)
    assert e.recommend(s, ["diagrams"])["recommended_content_id"] == "ct_sym_practice"


def test_when_every_lesson_was_tried_the_first_is_offered_again(e):
    s = state(tried={"diagrams": list(CONTENT["diagrams"])}, symbols=0.9, wiring=0.9, diagrams=0.3)
    assert e.recommend(s, ["diagrams"])["recommended_content_id"] == CONTENT["diagrams"][0]


# ---- repeat gaps ---------------------------------------------------------------------------


def test_repeat_gap_is_flagged_and_uses_a_new_lesson(e):
    s = state(tried={"diagrams": ["ct_diag_walk"]}, symbols=0.9, wiring=0.9, diagrams=0.4)
    rec = e.recommend_repeat(s, "diagrams", now_ms=5)
    assert rec["repeat_gap"] is True and rec["created_at"] == 5
    assert rec["recommended_content_id"] == "ct_diag_practice"
    assert "different way" in rec["diagnostic_text"]["en"]


def test_repeat_gap_is_returned_even_if_the_model_thinks_the_concept_is_fine(e):
    # "Got it!" pushed mastery up, but the follow-up check was failed: that still counts.
    s = state(tried={"diagrams": ["ct_diag_walk"]}, diagrams=0.75)
    rec = e.recommend_repeat(s, "diagrams")
    assert rec["repeat_gap"] is True and rec["concept_id"] == "diagrams"
    assert rec["recommended_content_id"] == "ct_diag_practice"


def test_repeat_gap_can_still_point_to_a_weak_prerequisite(e):
    s = state(tried={"diagrams": ["ct_diag_walk"]}, symbols=0.3, wiring=0.9, diagrams=0.4)
    rec = e.recommend_repeat(s, "diagrams")
    assert rec["repeat_gap"] is True and rec["chain"] == ["diagrams", "symbols"]


# ---- through the API ---------------------------------------------------------------------


def test_api_follows_the_same_rules():
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from circuit_coach.api import app

    client = TestClient(app)
    body = {
        "state": {"mastery": {"symbols": 0.3, "wiring": 0.9, "diagrams": 0.3}, "observations": {"symbols": 2, "wiring": 2, "diagrams": 2}, "tried": {"symbols": ["ct_sym_cards"]}},
        "module_id": "m3",
        "events": [],
    }
    rec = client.post("/v1/quiz-result", json=body).json()["recommendation"]
    assert rec["chain"] == ["diagrams", "symbols"] and rec["recommended_content_id"] == "ct_sym_practice"
    body["state"]["mastery"] = {"symbols": 0.9, "wiring": 0.9, "diagrams": 0.9}
    assert client.post("/v1/quiz-result", json=body).json()["recommendation"] is None
