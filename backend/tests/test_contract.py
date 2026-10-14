"""The committed API contract (docs/openapi.json) must match the running code."""

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from circuit_coach.api import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from export_openapi import OUT, render  # noqa: E402

client = TestClient(app)
SCHEMAS = app.openapi()["components"]["schemas"]


def test_committed_contract_is_up_to_date():
    assert OUT.exists(), "run python scripts/export_openapi.py"
    assert json.loads(OUT.read_text(encoding="utf8")) == json.loads(render()), "run python scripts/export_openapi.py"


def test_contract_lists_every_endpoint():
    paths = app.openapi()["paths"]
    assert {"/health", "/v1/concepts", "/v1/onboarding", "/v1/quiz-result", "/v1/got-it"} <= set(paths)


def _keys(name: str) -> set[str]:
    return set(SCHEMAS[name]["properties"])


def test_responses_carry_exactly_the_fields_in_the_contract():
    state = {"mastery": {"diagrams": 0.2}, "observations": {"diagrams": 2}, "tried": {}}
    health = client.get("/health").json()
    assert set(health) == _keys("HealthResponse")

    onboard = client.post("/v1/onboarding", json={"experience": "some", "events": []}).json()
    assert set(onboard) == _keys("OnboardingResponse") and set(onboard["state"]) == _keys("StateModel")

    events = [{"concept_tags": ["diagrams"], "is_correct": False}] * 3
    quiz = client.post("/v1/quiz-result", json={"state": state, "module_id": "m3", "events": events}).json()
    assert set(quiz) == _keys("QuizResultResponse")
    assert set(quiz["recommendation"]) == _keys("RecommendationModel")
    assert set(quiz["recommendation"]["diagnostic_text"]) == {"en", "hi"}

    got = client.post("/v1/got-it", json={"state": state, "concept_id": "diagrams"}).json()
    assert set(got) == _keys("GotItResponse")


def test_contract_matches_the_frontend_types():
    """The recommendation fields the frontend reads must all be in the contract."""
    types = ROOT.parent / "frontend" / "src" / "api" / "types.ts"
    if not types.exists():
        pytest.skip("frontend sources not present")
    text = types.read_text(encoding="utf8")
    block = text[text.index("export interface Recommendation {") :]
    block = block[: block.index("\n}")]
    import re

    ts_fields = set(re.findall(r"^\s+(\w+)\??:", block, re.M)) - {"from_trainer"}  # set only by the trainer console
    assert ts_fields == _keys("RecommendationModel")
