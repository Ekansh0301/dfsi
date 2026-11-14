"""API key, allowed browser origins and request size limits."""

import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from circuit_coach import api  # noqa: E402

EVENT = {"concept_tags": ["ohm"], "is_correct": False}


@pytest.fixture
def client():
    return TestClient(api.app)


def quiz(events):
    return {"state": {}, "module_id": "m2", "events": events}


def test_without_a_key_configured_calls_need_no_header(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEY", None)
    assert client.post("/v1/quiz-result", json=quiz([EVENT])).status_code == 200


def test_with_a_key_configured_v1_calls_need_it(client, monkeypatch):
    monkeypatch.setattr(api, "API_KEY", "s3cret")
    assert client.post("/v1/quiz-result", json=quiz([EVENT])).status_code == 401
    assert client.post("/v1/quiz-result", json=quiz([EVENT]), headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.post("/v1/quiz-result", json=quiz([EVENT]), headers={"X-API-Key": "s3cret"}).status_code == 200
    assert client.get("/health").status_code == 200  # health checks stay open


def test_browsers_are_limited_to_the_known_sites(client):
    ok = client.get("/health", headers={"Origin": "http://localhost:5173"})
    other = client.get("/health", headers={"Origin": "https://evil.example"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in other.headers


@pytest.mark.parametrize(
    "body",
    [
        quiz([EVENT] * (api.MAX_EVENTS + 1)),
        quiz([{"concept_tags": ["ohm"] * (api.MAX_TAGS + 1), "is_correct": True}]),
        {"state": {"tried": {"ohm": ["ct_ohm_walk"] * (api.MAX_TRIED + 1)}}, "module_id": "m2", "events": []},
        {"state": {"tried": {"ohm": ["x" * 65]}}, "module_id": "m2", "events": []},
    ],
)
def test_oversized_requests_are_rejected(client, body):
    assert client.post("/v1/quiz-result", json=body).status_code == 422


def test_a_full_quiz_is_well_within_the_limits(client):
    assert client.post("/v1/quiz-result", json=quiz([EVENT] * 50)).status_code == 200
