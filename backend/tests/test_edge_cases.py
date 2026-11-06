"""Edge cases with a defined behaviour (PLAN S4-1)."""

import json
from pathlib import Path

import pytest

from circuit_coach.bkt import HAND_SET
from circuit_coach.curriculum import CONCEPTS, CONTENT
from circuit_coach.engine import BASELINE, IMPROVED, Engine, Event, LearnerState
from circuit_coach.storage import Storage

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from circuit_coach import api  # noqa: E402

SAMPLE = Path(__file__).resolve().parents[1] / "datasets" / "barabari_sample"
BOTH = pytest.mark.parametrize("opt", [BASELINE, IMPROVED], ids=["baseline", "improved"])
client = TestClient(api.app)


def engine(opt) -> Engine:
    return Engine({c: HAND_SET for c in CONCEPTS}, options=opt)


# ---- all "I'm not sure" ---------------------------------------------------------------------


@BOTH
def test_all_unsure_placement_starts_at_the_first_module(opt):
    events = [Event((c,), False, unsure=True) for c in ("safety", "quantities", "ohm", "symbols", "wiring", "multimeter")]
    state, start = engine(opt).onboard("experienced", events)
    assert start == "m1"
    assert all(state.mastery[c] < 0.45 for c in ("safety", "symbols"))


@BOTH
def test_all_unsure_quick_check_recommends_a_lesson(opt):
    state = engine(opt).trace(LearnerState(), [Event(("symbols",), False, unsure=True)] * 3)
    assert engine(opt).recommend(state, ["symbols"])["concept_id"] == "symbols"


# ---- empty quick check ----------------------------------------------------------------------


@BOTH
def test_an_empty_quick_check_with_no_history_recommends_nothing(opt):
    assert engine(opt).recommend(LearnerState(), ["symbols", "wiring", "diagrams"]) is None


def test_empty_quiz_over_http_returns_the_state_unchanged_and_no_lesson():
    state = {"mastery": {"ohm": 0.9}, "observations": {"ohm": 3}, "tried": {}}
    body = client.post("/v1/quiz-result", json={"state": state, "module_id": "m3", "events": []}).json()
    assert body["state"] == state and body["recommendation"] is None


def test_an_empty_placement_starts_at_the_first_module():
    assert client.post("/v1/onboarding", json={"experience": "experienced", "events": []}).json()["start_module_id"] == "m1"


# ---- duplicate input -------------------------------------------------------------------------


@BOTH
def test_a_tag_listed_twice_counts_once(opt):
    state = engine(opt).trace(LearnerState(), [Event(("symbols", "symbols"), False)])
    assert state.observations == {"symbols": 1}


@pytest.fixture
def stored(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "store", Storage(f"sqlite:///{(tmp_path / 'c.db').as_posix()}"))
    return TestClient(api.app)


def test_a_resent_request_is_applied_once(stored):
    body = {
        "state": {},
        "module_id": "m3",
        "events": [{"concept_tags": ["diagrams"], "is_correct": False}],
        "learner_id": "asha",
        "request_id": "quiz-42",
    }
    first = stored.post("/v1/quiz-result", json=body).json()
    again = stored.post("/v1/quiz-result", json=body).json()
    assert again == first and first["state"]["observations"]["diagrams"] == 1
    assert stored.get("/v1/learners/asha/state").json()["observations"]["diagrams"] == 1
    other = stored.post("/v1/quiz-result", json={**body, "request_id": "quiz-43"}).json()
    assert other["state"]["observations"]["diagrams"] == 2


def test_the_same_barabari_attempt_sent_twice_is_applied_once(stored):
    quiz = json.loads((SAMPLE / "quiz_unit_m3.json").read_text(encoding="utf8"))
    attempt = json.loads((SAMPLE / "attempts.json").read_text(encoding="utf8"))["attempts"][0]
    a = stored.post("/v1/barabari/quiz-attempt", json={"state": {}, "quiz": quiz, "attempt": attempt}).json()
    b = stored.post("/v1/barabari/quiz-attempt", json={"state": {}, "quiz": quiz, "attempt": attempt}).json()
    assert a == b
    assert stored.get(f"/v1/learners/{attempt['student_id']}/state").json() == a["state"]


def test_without_storage_nothing_is_remembered_between_requests():
    """Stateless mode cannot recognise a repeat: the client must send each answer once."""
    body = {"state": {}, "module_id": "m3", "events": [{"concept_tags": ["diagrams"], "is_correct": False}], "request_id": "quiz-42"}
    a = client.post("/v1/quiz-result", json=body).json()
    b = client.post("/v1/quiz-result", json=body).json()
    assert a == b and a["state"]["observations"]["diagrams"] == 1


# ---- concepts with no prerequisites ---------------------------------------------------------


@BOTH
def test_a_root_concept_is_its_own_root_cause(opt):
    e = engine(opt)
    assert CONCEPTS["safety"]["prereqs"] == []
    state = e.trace(LearnerState(), [Event(("safety",), False)] * 3)
    rec = e.recommend(state, ["safety"])
    assert rec["chain"] == ["safety"] and rec["recommended_content_id"] == CONTENT["safety"][0]


@BOTH
def test_a_root_concept_always_learns_at_the_full_rate(opt):
    assert engine(opt).learn_rate(LearnerState(), "safety") in (None, HAND_SET.p_learn)


# ---- invalid input ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state",
    [{"mastery": {"ohm": 1.5}}, {"mastery": {"ohm": -0.1}}, {"observations": {"ohm": -1}}, {"mastery": {"nope": 0.5}}, {"tried": {"nope": []}}],
)
def test_impossible_states_are_rejected(state):
    assert client.post("/v1/quiz-result", json={"state": state, "module_id": "m3", "events": []}).status_code == 422


@pytest.mark.parametrize("raw", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_numbers_get_a_422_not_a_crash(raw):
    content = '{"state":{"mastery":{"ohm":' + raw + '}},"module_id":"m3","events":[]}'
    r = client.post("/v1/quiz-result", content=content, headers={"content-type": "application/json"})
    assert r.status_code == 422 and r.json()["detail"][0]["type"] == "finite_number"


@pytest.mark.parametrize(
    "event",
    [
        {"concept_tags": [], "is_correct": True},
        {"concept_tags": ["ohm"]},
        {"concept_tags": ["ohm"], "is_correct": True, "attempt_number": 0},
        {"concept_tags": ["ohm"], "is_correct": True, "score": -0.5},
        {"concept_tags": ["ohm"], "is_correct": True, "question_type": "essay"},
    ],
)
def test_invalid_events_are_rejected(event):
    assert client.post("/v1/quiz-result", json={"state": {}, "module_id": "m2", "events": [event]}).status_code == 422


def test_bad_experience_and_unknown_recheck_concept_are_rejected():
    assert client.post("/v1/onboarding", json={"experience": "expert", "events": []}).status_code == 422
    assert client.post("/v1/quiz-result", json={"state": {}, "module_id": "m1", "events": [], "recheck_concept": "nope"}).status_code == 422


def test_unknown_lesson_ids_in_tried_are_ignored():
    body = {"state": {"tried": {"ohm": ["not_a_lesson"]}}, "module_id": "m2", "events": [{"concept_tags": ["ohm"], "is_correct": False}] * 3}
    assert client.post("/v1/quiz-result", json=body).json()["recommendation"]["recommended_content_id"] == CONTENT["ohm"][0]


def test_a_huge_attempt_number_counts_for_nothing_but_is_accepted():
    body = {
        "state": {"mastery": {"ohm": 0.5}, "observations": {"ohm": 1}},
        "module_id": "m2",
        "events": [{"concept_tags": ["ohm"], "is_correct": True, "attempt_number": 10**9}],
    }
    out = client.post("/v1/quiz-result", json=body).json()["state"]["mastery"]["ohm"]
    assert out == pytest.approx(0.5 + 0.5 * api.engine.params["ohm"].p_learn)
