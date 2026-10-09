import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from circuit_coach.api import app  # noqa: E402

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_concepts_lists_graph_modules_and_lessons():
    body = client.get("/v1/concepts").json()
    assert body["concepts"]["diagrams"]["prereqs"] == ["symbols", "wiring"]
    assert "m3" in body["modules"] and "diagrams" in body["content"]


def test_onboarding_returns_state_and_start_module():
    r = client.post("/v1/onboarding", json={"experience": "new", "events": [{"concept_tags": ["safety"], "is_correct": True}]})
    assert r.status_code == 200
    body = r.json()
    assert body["start_module_id"].startswith("m") and "safety" in body["state"]["mastery"]


def test_quiz_result_recommends_for_a_weak_concept_and_updates_state():
    events = [{"concept_tags": ["diagrams"], "is_correct": False}] * 3
    r = client.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": events, "now": 7})
    body = r.json()
    assert body["recommendation"]["concept_id"] == "diagrams"
    assert body["recommendation"]["created_at"] == 7
    assert body["state"]["observations"]["diagrams"] == 3


def test_failed_recheck_gives_a_repeat_gap_recommendation():
    r = client.post(
        "/v1/quiz-result",
        json={"state": {"tried": {"diagrams": ["ct_diag_walk"]}}, "module_id": "m5", "events": [], "recheck_concept": "diagrams"},
    )
    rec = r.json()["recommendation"]
    assert rec["repeat_gap"] is True and rec["recommended_content_id"] != "ct_diag_walk"


def test_got_it_applies_a_learning_step():
    base = {"mastery": {"diagrams": 0.2}}
    r = client.post("/v1/got-it", json={"state": base, "concept_id": "diagrams"})
    assert r.json()["state"]["mastery"]["diagrams"] > 0.2


def test_unknown_concept_is_rejected():
    r = client.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": [{"concept_tags": ["nope"], "is_correct": True}]})
    assert r.status_code == 422


def test_unknown_module_is_404():
    assert client.post("/v1/quiz-result", json={"state": {}, "module_id": "m99", "events": []}).status_code == 404
