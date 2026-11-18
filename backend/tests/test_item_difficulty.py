"""Per-question difficulty reaches the served model and can be estimated from stored answers."""

import json
import sys
from pathlib import Path

import pytest

from circuit_coach import api, barabari
from circuit_coach.engine import load_item_difficulty
from circuit_coach.storage import Storage

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import estimate_item_difficulty as est  # noqa: E402

SAMPLE = Path(__file__).resolve().parents[1] / "datasets" / "barabari_sample"


@pytest.fixture
def client():
    return TestClient(api.app)


@pytest.fixture
def table(monkeypatch):
    """A difficulty table on the service's engines for the length of one test."""
    t = {"hard_q": 1.5, "easy_q": -1.5}
    for eng in api.engines.values():
        monkeypatch.setattr(eng, "item_difficulty", t)
    return t


def mastery(client, model: str, item_id: str | None, correct: bool = False) -> float:
    ev = {"concept_tags": ["ohm"], "is_correct": correct}
    if item_id:
        ev["item_id"] = item_id
    r = client.post(f"/v1/quiz-result?model={model}", json={"state": {}, "module_id": "m2", "events": [ev]})
    assert r.status_code == 200
    return r.json()["state"]["mastery"]["ohm"]


def test_the_shipped_table_loads_and_is_well_formed():
    t = load_item_difficulty()
    assert all(isinstance(k, str) and isinstance(v, float) for k, v in t.items())


def test_a_known_question_moves_the_improved_model(client, table):
    base = mastery(client, "improved", None)
    hard, easy = mastery(client, "improved", "hard_q"), mastery(client, "improved", "easy_q")
    assert hard != base and easy != base and hard != easy
    # a wrong answer on a hard question says less than on an easy one
    assert hard > easy


def test_an_unknown_question_counts_as_average(client, table):
    assert mastery(client, "improved", "not_in_the_table") == mastery(client, "improved", None)


def test_the_baseline_ignores_difficulty(client, table):
    assert mastery(client, "baseline", "hard_q") == mastery(client, "baseline", None)


def test_a_marked_answer_accepts_its_question_id(client, table):
    def marked(item):
        body = {"state": {}, "concept_tags": ["ohm"], "score": 0.0}
        if item:
            body["item_id"] = item
        r = client.post("/v1/marked-answer?model=improved", json=body)
        assert r.status_code == 200
        return r.json()["state"]["mastery"]["ohm"]

    assert marked("hard_q") != marked(None)
    assert marked("not_in_the_table") == marked(None)


def test_barabari_attempts_carry_their_question_ids():
    quiz = barabari.parse_quiz(json.loads((SAMPLE / "quiz_unit_m3.json").read_text(encoding="utf8")))
    attempt = barabari.parse_attempt(json.loads((SAMPLE / "attempts.json").read_text(encoding="utf8"))["attempts"][0])
    events = barabari.attempt_events(quiz, attempt, barabari.TagMap.load())
    assert events and all(e.item_id and e.item_id.startswith(quiz.id + "/") for e in events)


# ---- estimating the table from stored answers ----------------------------------------------


def log_quiz(client, learner: str, answers: list[tuple[str, bool]]):
    events = [{"concept_tags": ["ohm"], "is_correct": ok, "item_id": q} for q, ok in answers]
    r = client.post("/v1/quiz-result", json={"state": {}, "module_id": "m2", "events": events, "learner_id": learner})
    assert r.status_code == 200


def test_a_question_answered_wrong_more_often_is_estimated_harder(tmp_path, monkeypatch):
    store = Storage(f"sqlite:///{(tmp_path / 'coach.db').as_posix()}")
    monkeypatch.setattr(api, "store", store)
    c = TestClient(api.app)
    for n in range(40):
        # q_hard: right 1 time in 4; q_easy: right 9 times in 10; both on the same concept
        log_quiz(c, f"l{n}", [("q_hard", n % 4 == 0), ("q_easy", n % 10 != 0)])
    table = est.estimate(store.steps())
    assert set(table) == {"q_hard", "q_easy"}
    assert table["q_hard"] > 0 > table["q_easy"]


def test_only_first_attempts_count(tmp_path, monkeypatch):
    store = Storage(f"sqlite:///{(tmp_path / 'coach.db').as_posix()}")
    monkeypatch.setattr(api, "store", store)
    c = TestClient(api.app)
    for n in range(30):
        ev = {"concept_tags": ["ohm"], "is_correct": True, "item_id": "q_retaken", "attempt_number": 2}
        c.post("/v1/quiz-result", json={"state": {}, "module_id": "m2", "events": [ev], "learner_id": f"r{n}"})
    assert est.estimate(store.steps()) == {}


def test_answers_come_from_every_kind_of_step(tmp_path, monkeypatch):
    store = Storage(f"sqlite:///{(tmp_path / 'coach.db').as_posix()}")
    monkeypatch.setattr(api, "store", store)
    c = TestClient(api.app)
    c.post("/v1/onboarding", json={"experience": "some", "events": [{"concept_tags": ["ohm"], "is_correct": True, "item_id": "q_a"}], "learner_id": "x"})
    c.post("/v1/marked-answer", json={"state": {}, "concept_tags": ["ohm"], "score": 0.75, "item_id": "q_b", "learner_id": "x"})
    quiz = json.loads((SAMPLE / "quiz_unit_m3.json").read_text(encoding="utf8"))
    attempt = json.loads((SAMPLE / "attempts.json").read_text(encoding="utf8"))["attempts"][0]
    c.post("/v1/barabari/quiz-attempt", json={"state": {}, "quiz": quiz, "attempt": attempt})
    items = {a[0] for st in store.steps() for a in est.answers_of(st)}
    assert {"q_a", "q_b"} <= items and any(i.startswith(quiz["id"] + "/") for i in items)


def test_the_script_writes_the_report_and_only_writes_the_shipped_tables_on_request(tmp_path, monkeypatch):
    out = {"report": tmp_path / "report.json", "service": tmp_path / "service.json", "browser": tmp_path / "browser.json"}
    monkeypatch.setattr(est, "REPORT", out["report"])
    monkeypatch.setattr(est, "SERVICE_TABLE", out["service"])
    monkeypatch.setattr(est, "BROWSER_TABLE", out["browser"])
    store = Storage(f"sqlite:///{(tmp_path / 'coach.db').as_posix()}")
    monkeypatch.setattr(api, "store", store)
    c = TestClient(api.app)
    for n in range(20):
        log_quiz(c, f"l{n}", [("q_hard", n % 4 == 0), ("q_easy", True)])
    url = f"sqlite:///{(tmp_path / 'coach.db').as_posix()}"
    monkeypatch.setattr(sys, "argv", ["estimate_item_difficulty.py", "--db", url])
    est.main()
    assert out["report"].exists() and not out["service"].exists() and not out["browser"].exists()
    monkeypatch.setattr(sys, "argv", ["estimate_item_difficulty.py", "--db", url, "--write-service-table"])
    est.main()
    assert out["service"].read_text() == out["browser"].read_text()
    assert set(json.loads(out["service"].read_text())["items"]) == {"q_hard", "q_easy"}
