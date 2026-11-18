"""Write the golden cases that tie the browser engine to the service.

    python scripts/export_parity_cases.py

Each case is a short journey (onboarding, quick checks, "Got it!", marked answers, a repeat gap)
sent to the real API under one model, with the state and recommendation it answered at every
step. `frontend/src/engine/__tests__/parity.test.ts` replays the same journeys on the browser
engine and requires the same answers; `tests/test_parity.py` fails if this file is out of date.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from circuit_coach import api
from circuit_coach.curriculum import CONCEPTS, CONTENT, MODULES

OUT = Path(__file__).resolve().parents[2] / "frontend" / "src" / "engine" / "__tests__" / "parity_cases.json"
CONCEPT_IDS = list(CONCEPTS)
ITEMS = [f"i{n}" for n in range(1, 9)]
TYPES = ["multiple_choice"] * 5 + ["true_false", "short_answer"]
NOW = 1_700_000_000_000


def event(rng: np.random.Generator, concepts: list[str]) -> dict:
    n_tags = int(rng.choice([1, 1, 1, 2, 3]))
    tags = [str(c) for c in rng.choice(concepts, size=min(n_tags, len(concepts)), replace=False)]
    qtype = str(rng.choice(TYPES))
    ev: dict = {"concept_tags": tags, "is_correct": bool(rng.random() < 0.55), "question_type": qtype, "item_id": str(rng.choice(ITEMS))}
    if rng.random() < 0.2:
        ev["unsure"] = True
        ev["is_correct"] = False
    if qtype == "short_answer" and rng.random() < 0.8:
        ev["score"] = float(rng.choice([0, 0.25, 0.5, 0.75, 1]))
    if rng.random() < 0.25:
        ev["attempt_number"] = int(rng.integers(2, 4))
    return ev


def journey(rng: np.random.Generator) -> list[dict]:
    ops: list[dict] = []
    ops.append({"op": "onboard", "experience": str(rng.choice(["new", "some", "experienced"])), "events": [event(rng, CONCEPT_IDS) for _ in range(int(rng.integers(0, 7)))]})
    for _ in range(int(rng.integers(2, 6))):
        mid = str(rng.choice(list(MODULES)))
        concepts = MODULES[mid]["concepts"]
        kind = rng.random()
        if kind < 0.7:
            ops.append({"op": "quiz", "module_id": mid, "events": [event(rng, concepts + CONCEPT_IDS[:2]) for _ in range(int(rng.integers(0, 7)))]})
        elif kind < 0.85:
            c = str(rng.choice(CONCEPT_IDS))
            ops.append({"op": "got_it", "concept_id": c, "content_id": str(CONTENT[c][0])})
            ops.append({"op": "quiz", "module_id": mid, "recheck_concept": c, "events": [event(rng, [c]) for _ in range(int(rng.integers(1, 3)))]})
        else:
            tags = [str(c) for c in rng.choice(concepts, size=min(2, len(concepts)), replace=False)]
            ops.append({"op": "marked", "concept_tags": tags, "score": float(rng.choice([0, 0.25, 0.5, 0.75, 1])), "attempt_number": int(rng.integers(1, 3)), "item_id": str(rng.choice(ITEMS))})
    return ops


def run(client: TestClient, model: str, ops: list[dict]) -> list[dict]:
    state: dict = {}
    steps = []
    for op in ops:
        kind = op["op"]
        if kind == "onboard":
            r = client.post(f"/v1/onboarding?model={model}", json={"experience": op["experience"], "events": op["events"]})
            body = r.json()
            state = body["state"]
            steps.append({"op": op, "status": r.status_code, "state": state, "start_module_id": body["start_module_id"]})
        elif kind == "quiz":
            req = {"state": state, "module_id": op["module_id"], "events": op["events"], "now": NOW}
            if op.get("recheck_concept"):
                req["recheck_concept"] = op["recheck_concept"]
            r = client.post(f"/v1/quiz-result?model={model}", json=req)
            body = r.json()
            state = body["state"]
            steps.append({"op": op, "status": r.status_code, "state": state, "recommendation": body["recommendation"]})
        elif kind == "got_it":
            r = client.post(f"/v1/got-it?model={model}", json={"state": state, "concept_id": op["concept_id"], "content_id": op["content_id"]})
            state = r.json()["state"]
            steps.append({"op": op, "status": r.status_code, "state": state})
        else:
            req = {"state": state, "concept_tags": op["concept_tags"], "score": op["score"], "attempt_number": op["attempt_number"], "item_id": op["item_id"], "now": NOW}
            r = client.post(f"/v1/marked-answer?model={model}", json=req)
            body = r.json()
            state = body["state"]
            steps.append({"op": op, "status": r.status_code, "state": state, "recommendation": body["recommendation"]})
    return steps


def build(n_cases: int = 60, seed: int = 7) -> dict:
    client = TestClient(api.app)
    rng = np.random.default_rng(seed)
    saved = {name: eng.item_difficulty for name, eng in api.engines.items()}
    cases = []
    try:
        for k in range(n_cases):
            difficulty = {i: round(float(rng.uniform(-1.5, 1.5)), 3) for i in ITEMS if rng.random() < 0.6} if k % 2 else {}
            ops = journey(rng)
            for model in ("improved", "baseline"):
                for eng in api.engines.values():
                    eng.item_difficulty = dict(difficulty)
                cases.append({"model": model, "difficulty": difficulty, "steps": run(client, model, ops)})
    finally:
        for name, eng in api.engines.items():
            eng.item_difficulty = saved[name]
    return {"note": "Generated by backend/scripts/export_parity_cases.py from the running API. Do not edit.", "cases": cases}


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
