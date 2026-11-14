"""Optional learner storage (PLAN S4-4): SQLite now, PostgreSQL by changing the URL."""

import json
from pathlib import Path

import pytest

from circuit_coach.engine import LearnerState
from circuit_coach.storage import Storage

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from circuit_coach import api  # noqa: E402

SAMPLE = Path(__file__).resolve().parents[1] / "datasets" / "barabari_sample"


@pytest.fixture
def db_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'coach.db').as_posix()}"


@pytest.fixture
def client(db_url, monkeypatch):
    monkeypatch.setattr(api, "store", Storage(db_url))
    return TestClient(api.app)


def test_state_round_trips_and_survives_a_restart(db_url):
    Storage(db_url).save("asha", LearnerState({"ohm": 0.4}, {"ohm": 2}, {"ohm": ["ct_ohm_walk"]}))
    again = Storage(db_url)  # a new connection, as after a service restart
    assert again.load("asha") == LearnerState({"ohm": 0.4}, {"ohm": 2}, {"ohm": ["ct_ohm_walk"]})
    assert again.load("nobody") is None


def test_saving_twice_updates_the_row(db_url):
    s = Storage(db_url)
    s.save("asha", LearnerState({"ohm": 0.4}, {"ohm": 1}))
    s.save("asha", LearnerState({"ohm": 0.7}, {"ohm": 2}))
    assert s.load("asha").mastery == {"ohm": 0.7}


def test_a_learner_id_with_an_empty_state_continues_from_the_saved_state(client):
    events = [{"concept_tags": ["diagrams"], "is_correct": False}] * 2
    first = client.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": events, "learner_id": "asha"}).json()
    second = client.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": events, "learner_id": "asha"}).json()
    assert first["state"]["observations"]["diagrams"] == 2
    assert second["state"]["observations"]["diagrams"] == 4
    assert client.get("/v1/learners/asha/state").json() == second["state"]


def test_a_sent_state_still_wins_over_the_saved_one(client):
    client.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": [{"concept_tags": ["diagrams"], "is_correct": False}], "learner_id": "asha"})
    body = {"state": {"observations": {"ohm": 5}, "mastery": {"ohm": 0.9}}, "module_id": "m2", "events": [], "learner_id": "asha"}
    out = client.post("/v1/quiz-result", json=body).json()
    assert out["state"]["observations"] == {"ohm": 5}


def test_every_step_is_logged(client):
    client.post("/v1/onboarding", json={"experience": "new", "events": [], "learner_id": "ravi"})
    client.post("/v1/got-it?model=improved", json={"state": {}, "concept_id": "ohm", "learner_id": "ravi"})
    client.post("/v1/marked-answer", json={"state": {}, "concept_tags": ["ohm"], "score": 0.5, "learner_id": "ravi"})
    steps = api.store.history("ravi")
    assert [s["step"] for s in steps] == ["onboarding", "got-it", "marked-answer"]
    assert [s["model"] for s in steps] == ["baseline", "improved", "baseline"]


def test_barabari_attempts_are_stored_under_the_student_id(client):
    quiz = json.loads((SAMPLE / "quiz_unit_m3.json").read_text(encoding="utf8"))
    attempt = json.loads((SAMPLE / "attempts.json").read_text(encoding="utf8"))["attempts"][1]
    client.post("/v1/barabari/quiz-attempt", json={"state": {}, "quiz": quiz, "attempt": attempt})
    assert client.get(f"/v1/learners/{attempt['student_id']}/state").json()["observations"]["diagrams"] == 2


def test_without_storage_the_service_stays_stateless(monkeypatch):
    monkeypatch.setattr(api, "store", None)
    c = TestClient(api.app)
    events = [{"concept_tags": ["diagrams"], "is_correct": False}]
    one = c.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": events, "learner_id": "asha"}).json()
    two = c.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": events, "learner_id": "asha"}).json()
    assert one["state"] == two["state"]
    assert c.get("/v1/learners/asha/state").status_code == 404


def test_unknown_learner_is_404(client):
    assert client.get("/v1/learners/nobody/state").status_code == 404


def test_a_repeat_gap_with_stored_state_gets_a_lesson_not_yet_tried(client):
    wrong = [{"concept_tags": ["diagrams"], "is_correct": False}] * 2
    first = client.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": wrong, "learner_id": "ravi"}).json()
    lesson = first["recommendation"]["recommended_content_id"]
    client.post("/v1/got-it", json={"state": {}, "concept_id": "diagrams", "content_id": lesson, "learner_id": "ravi"})
    recheck = {"state": {}, "module_id": "m3", "events": wrong[:1], "recheck_concept": "diagrams", "learner_id": "ravi"}
    again = client.post("/v1/quiz-result", json=recheck).json()["recommendation"]
    assert again["repeat_gap"] is True
    assert again["recommended_content_id"] != lesson
    assert client.get("/v1/learners/ravi/state").json()["tried"]["diagrams"] == [lesson]


def test_got_it_rejects_a_lesson_from_another_concept(client):
    r = client.post("/v1/got-it", json={"state": {}, "concept_id": "ohm", "content_id": "ct_sym_cards"})
    assert r.status_code == 422
