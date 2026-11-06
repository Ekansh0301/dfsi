"""The Sprint 3 model options (PLAN S3-2, S3-3, S3-5, S3-6) and the model switch (S3-7)."""

import pytest

from circuit_coach import bkt, prediction
from circuit_coach.bkt import HAND_SET, BKTParams
from circuit_coach.curriculum import CONCEPTS
from circuit_coach.engine import BASELINE, IMPROVED, MODELS, WEAK, Engine, Event, LearnerState, ModelOptions, load_params


def engine(options: ModelOptions = BASELINE, **kw) -> Engine:
    return Engine({c: HAND_SET for c in CONCEPTS}, options=options, **kw)


# ---- S3-2: first-tag credit -----------------------------------------------------------------


def test_first_tag_credit_updates_only_the_main_concept():
    e = engine(ModelOptions(credit="first"))
    out = e.trace(LearnerState(), [Event(("diagrams", "symbols"), False)])
    assert set(out.observations) == {"diagrams"}


def test_baseline_still_credits_every_tag():
    out = engine().trace(LearnerState(), [Event(("diagrams", "symbols"), False)])
    assert set(out.observations) == {"diagrams", "symbols"}


def test_a_wrong_two_concept_answer_no_longer_blames_a_known_prerequisite():
    state = LearnerState({"symbols": 0.9, "wiring": 0.9}, {"symbols": 3, "wiring": 3})
    events = [Event(("diagrams", "symbols"), False)] * 2
    base = engine().trace(state, events)
    first = engine(ModelOptions(credit="first")).trace(state, events)
    assert base.mastery["symbols"] < first.mastery["symbols"] == 0.9


# ---- S3-3: question difficulty ---------------------------------------------------------------


def test_harder_questions_slip_more_and_are_guessed_less():
    easy, hard = bkt.slip_guess(HAND_SET, difficulty=-1.0), bkt.slip_guess(HAND_SET, difficulty=1.0)
    assert hard[0] > HAND_SET.p_slip > easy[0]
    assert hard[1] < HAND_SET.p_guess < easy[1]
    assert bkt.slip_guess(HAND_SET) == (HAND_SET.p_slip, HAND_SET.p_guess)


def test_true_false_guess_stays_at_one_half_whatever_the_difficulty():
    assert bkt.slip_guess(HAND_SET, "true_false", 1.5)[1] == 0.5


def test_a_right_answer_on_a_hard_question_is_stronger_evidence():
    assert bkt.update(0.4, True, HAND_SET, difficulty=1.0) > bkt.update(0.4, True, HAND_SET, difficulty=-1.0)


def test_item_difficulty_is_used_only_when_switched_on():
    events = [Event(("ohm",), True, item_id="hard_q")]
    on = engine(ModelOptions(item_difficulty=True), item_difficulty={"hard_q": 1.5}).trace(LearnerState(), events)
    off = engine(item_difficulty={"hard_q": 1.5}).trace(LearnerState(), events)
    assert on.mastery["ohm"] > off.mastery["ohm"]


def test_difficulty_estimates_follow_correct_rates():
    train = [[("easy", ("c",), 1), ("hard", ("c",), 0)] for _ in range(50)] + [[("easy", ("c",), 1), ("hard", ("c",), 1)] for _ in range(10)]
    d = prediction.estimate_item_difficulty(train)
    assert d["hard"] > 0 > d["easy"]


# ---- S3-5: prerequisite-aware learning -------------------------------------------------------


def test_learning_is_slower_while_an_observed_prerequisite_is_weak():
    e = engine(ModelOptions(prereq_learn_factor=0.5))
    weak = LearnerState({"symbols": 0.1, "wiring": 0.1}, {"symbols": 2, "wiring": 2})
    strong = LearnerState({"symbols": 0.99, "wiring": 0.99}, {"symbols": 2, "wiring": 2})
    assert e.learn_rate(weak, "diagrams") < e.learn_rate(strong, "diagrams") <= HAND_SET.p_learn
    assert e.learn_rate(weak, "diagrams") >= 0.5 * HAND_SET.p_learn


def test_unobserved_prerequisites_do_not_slow_learning():
    e = engine(ModelOptions(prereq_learn_factor=0.5))
    assert e.learn_rate(LearnerState(), "diagrams") == pytest.approx(HAND_SET.p_learn)


def test_factor_one_switches_it_off():
    assert engine().learn_rate(LearnerState({"symbols": 0.1}, {"symbols": 1}), "diagrams") is None


# ---- S3-6: more evidence before a lesson ----------------------------------------------------


def test_one_borderline_answer_is_not_enough_for_a_lesson():
    e = engine(ModelOptions(min_evidence=2, strong_evidence=0.4))
    one = LearnerState({"diagrams": 0.5}, {"diagrams": 1})
    assert e.recommend(one, ["diagrams"]) is None
    assert engine().recommend(one, ["diagrams"]) is not None


def test_two_answers_or_a_very_low_mastery_are_enough():
    e = engine(ModelOptions(min_evidence=2, strong_evidence=0.4))
    assert e.recommend(LearnerState({"diagrams": 0.5}, {"diagrams": 2}), ["diagrams"])["concept_id"] == "diagrams"
    assert e.recommend(LearnerState({"diagrams": 0.3}, {"diagrams": 1}), ["diagrams"])["concept_id"] == "diagrams"


def test_unobserved_concepts_are_never_a_gap_under_the_evidence_rule():
    e = engine(ModelOptions(min_evidence=2, strong_evidence=0.4))
    assert e.recommend(LearnerState(), ["diagrams"]) is None
    assert engine().recommend(LearnerState(), ["diagrams"]) is not None  # the baseline quirk


# ---- S3-7: the improved model and the switch ------------------------------------------------


def test_improved_model_settings():
    assert IMPROVED.credit == "first" and IMPROVED.item_difficulty
    assert IMPROVED.prereq_learn_factor == 0.5 and (IMPROVED.min_evidence, IMPROVED.strong_evidence) == (2, 0.4)
    assert set(MODELS) == {"baseline", "improved"} and MODELS["baseline"] == BASELINE


def test_improved_model_keeps_the_demo_scenarios():
    """Direct gap and hidden cause still end the same way with the improved model."""
    e = engine(IMPROVED)
    placement = [Event((c,), True) for c in ("safety", "quantities", "ohm", "symbols", "wiring", "multimeter")]
    state, _ = e.onboard("some", placement)
    direct = e.trace(state, [Event(("symbols",), True), Event(("wiring", "safety"), True), Event(("diagrams", "symbols"), False), Event(("diagrams",), False), Event(("wiring",), True)])
    assert e.recommend(direct, ["symbols", "wiring", "diagrams"])["concept_id"] == "diagrams"
    state, _ = e.onboard("some", [Event((c,), c != "symbols") for c in ("safety", "quantities", "ohm", "symbols", "wiring", "multimeter")])
    hidden = e.trace(state, [Event(("symbols",), False), Event(("wiring", "safety"), True), Event(("diagrams", "symbols"), False), Event(("diagrams",), False), Event(("wiring",), True)])
    rec = e.recommend(hidden, ["symbols", "wiring", "diagrams"])
    assert rec["concept_id"] == "symbols" and rec["chain"] == ["diagrams", "symbols"]


def test_improved_parameters_fall_back_to_the_baseline_ones(tmp_path):
    f = tmp_path / "p.json"
    f.write_text('{"concepts": {"ohm": {"p_init": 0.1, "p_learn": 0.2, "p_slip": 0.3, "p_guess": 0.2}}}')
    assert load_params(f, "improved")["ohm"] == BKTParams(0.1, 0.2, 0.3, 0.2)
    f.write_text('{"concepts": {"ohm": {"p_init": 0.1, "p_learn": 0.2, "p_slip": 0.3, "p_guess": 0.2}}, "concepts_first_tag": {"ohm": {"p_init": 0.1, "p_learn": 0.2, "p_slip": 0.1, "p_guess": 0.2}}}')
    assert load_params(f, "improved")["ohm"].p_slip == 0.1 and load_params(f, "baseline")["ohm"].p_slip == 0.3


@pytest.fixture
def client():
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from circuit_coach.api import app

    return TestClient(app)


def test_health_reports_the_default_and_available_models(client):
    body = client.get("/health").json()
    assert body["model"] == "baseline" and body["models"] == ["baseline", "improved"]


def test_a_request_can_choose_the_model(client):
    body = {"state": {}, "module_id": "m3", "events": [{"concept_tags": ["diagrams", "symbols"], "is_correct": False}]}
    base = client.post("/v1/quiz-result", json=body).json()
    imp = client.post("/v1/quiz-result?model=improved", json=body).json()
    assert set(base["state"]["observations"]) == {"diagrams", "symbols"}
    assert set(imp["state"]["observations"]) == {"diagrams"}
    assert client.post("/v1/quiz-result?model=other", json=body).status_code == 422


def test_every_engine_endpoint_accepts_the_model(client):
    assert client.post("/v1/onboarding?model=improved", json={"experience": "new", "events": []}).status_code == 200
    assert client.post("/v1/got-it?model=improved", json={"state": {}, "concept_id": "ohm"}).status_code == 200

