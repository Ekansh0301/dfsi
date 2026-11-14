"""Barabari's quiz format: question types, partial credit, retakes and concept tags (PLAN S3-4)."""

import copy
import json
from pathlib import Path

import pytest

from circuit_coach import barabari as b
from circuit_coach import bkt
from circuit_coach.bkt import BKTParams
from circuit_coach.curriculum import CONCEPTS
from circuit_coach.engine import Engine, Event, LearnerState

SAMPLE = Path(__file__).resolve().parents[1] / "datasets" / "barabari_sample"
P = BKTParams(p_init=0.3, p_learn=0.1, p_slip=0.1, p_guess=0.2)


def quiz_dict() -> dict:
    return json.loads((SAMPLE / "quiz_unit_m3.json").read_text(encoding="utf8"))


def attempts() -> list[dict]:
    return json.loads((SAMPLE / "attempts.json").read_text(encoding="utf8"))["attempts"]


@pytest.fixture
def quiz() -> b.Quiz:
    return b.parse_quiz(quiz_dict())


# ---- update rules ------------------------------------------------------------------------


def test_true_false_right_answer_is_weaker_evidence_than_multiple_choice():
    mc = bkt.update(0.4, True, P, question_type="multiple_choice")
    tf = bkt.update(0.4, True, P, question_type="true_false")
    assert bkt.guess_for(P, "true_false") == 0.5
    assert 0.4 < tf < mc


def test_a_right_short_answer_is_strong_evidence():
    assert bkt.update(0.4, True, P, question_type="short_answer") > bkt.update(0.4, True, P, question_type="multiple_choice")


def test_partial_credit_mixes_the_right_and_wrong_posteriors():
    right = bkt.posterior(0.4, True, P, guess=0.05)
    wrong = bkt.posterior(0.4, False, P, guess=0.05)
    assert bkt.evidence(0.4, False, P, score=0.6, question_type="short_answer") == pytest.approx(0.6 * right + 0.4 * wrong)


def test_partial_credit_is_monotone_and_full_marks_equal_a_right_answer():
    ups = [bkt.update(0.4, False, P, score=s, question_type="short_answer") for s in (0.0, 0.25, 0.5, 0.75, 1.0)]
    assert ups == sorted(ups)
    assert ups[-1] == pytest.approx(bkt.update(0.4, True, P, question_type="short_answer"))
    assert ups[0] == pytest.approx(bkt.update(0.4, False, P, question_type="short_answer"))


def test_score_overrides_is_correct():
    assert bkt.update(0.4, True, P, score=0.0) == pytest.approx(bkt.update(0.4, False, P))


def test_retakes_count_for_less():
    first = bkt.evidence(0.4, True, P, attempt=1)
    second = bkt.evidence(0.4, True, P, attempt=2)
    third = bkt.evidence(0.4, True, P, attempt=3)
    assert 0.4 < third < second < first
    assert second - 0.4 == pytest.approx((first - 0.4) * bkt.RETAKE_DECAY)


def test_defaults_keep_the_original_update():
    post = 0.4 * 0.9 / (0.4 * 0.9 + 0.6 * 0.2)
    assert bkt.update(0.4, True, P) == pytest.approx(post + (1 - post) * 0.1)


def test_engine_passes_the_new_fields_to_every_tag():
    e = Engine({c: bkt.HAND_SET for c in CONCEPTS})
    plain = e.trace(LearnerState(), [Event(("symbols", "wiring"), True)])
    tf = e.trace(LearnerState(), [Event(("symbols", "wiring"), True, question_type="true_false")])
    assert tf.mastery["symbols"] < plain.mastery["symbols"] and tf.mastery["wiring"] < plain.mastery["wiring"]


# ---- reading and validating the format -----------------------------------------------------


def test_sample_quiz_is_valid(quiz):
    assert b.validate_quiz(quiz) == []
    assert {q.question_type for q in quiz.questions} == {"multiple_choice", "true_false", "short_answer"}


@pytest.mark.parametrize(
    "breaks, message",
    [
        (lambda d: d["questions"][0]["options"][1].update(is_correct=True), "exactly one correct"),
        (lambda d: d["questions"][0].update(options=d["questions"][0]["options"][:1]), "2 to 6 options"),
        (lambda d: d["questions"][2]["options"].append({"id": "x", "option_text": "Maybe", "is_correct": False}), "true_false needs two"),
        (lambda d: d["questions"][4]["options"].append({"id": "x", "option_text": "A", "is_correct": True}), "short_answer takes no options"),
        (lambda d: d["questions"][1].update(question_type="essay"), "unknown question_type"),
        (lambda d: d.update(passing_score=120), "passing_score"),
        (lambda d: d["questions"][1].update(id="q_01"), "duplicate question ids"),
    ],
)
def test_validation_catches_broken_quizzes(breaks, message):
    d = copy.deepcopy(quiz_dict())
    breaks(d)
    assert any(message in p for p in b.validate_quiz(b.parse_quiz(d)))


def test_the_pdf_example_quiz_parses():
    """The JavaScript quiz from Barabari's format document, field for field."""
    d = {
        "id": "quiz_u101_js_fundamentals",
        "unit_id": "unit_4829ad20",
        "title": "Unit 1: JavaScript Execution Context & Scope Quiz",
        "passing_score": 60,
        "max_score": 100,
        "questions": [
            {"id": "q_01", "question_text": "typeof NaN?", "question_type": "multiple_choice", "points": 25, "explanation": "...",
             "options": [{"id": "opt_1a", "option_text": "'undefined'", "is_correct": False}, {"id": "opt_1b", "option_text": "'number'", "is_correct": True},
                         {"id": "opt_1c", "option_text": "'NaN'", "is_correct": False}, {"id": "opt_1d", "option_text": "'object'", "is_correct": False}]},
            {"id": "q_02", "question_text": "const ...", "question_type": "true_false", "points": 25, "explanation": "...",
             "options": [{"id": "opt_2a", "option_text": "True", "is_correct": False}, {"id": "opt_2b", "option_text": "False", "is_correct": True}]},
        ],
    }
    assert b.validate_quiz(b.parse_quiz(d)) == []


# ---- grading, tags and events --------------------------------------------------------------


def test_scores_follow_barabari_rules(quiz):
    a, bb, retake, full = (b.parse_attempt(x) for x in attempts())
    assert b.attempt_score(quiz, a) == {"points": 64.0, "max_score": 100.0, "percent": 64.0, "passed": True, "awaiting_review_points": 0.0, "answers_revealed": False}
    assert b.attempt_score(quiz, bb)["passed"] is False  # 52 is below the 60 pass mark
    assert b.attempt_score(quiz, retake)["awaiting_review_points"] == 20.0
    assert b.attempt_score(quiz, full)["percent"] == 100.0


def test_answers_are_revealed_from_the_third_attempt(quiz):
    third = b.parse_attempt({**attempts()[0], "attempt_number": b.MIN_ATTEMPTS_FOR_REVEAL})
    assert b.attempt_score(quiz, third)["answers_revealed"] is True


def test_question_tags_win_over_unit_tags(quiz):
    tags = b.TagMap.load()
    assert tags.tags_for(quiz, quiz.question("q_01")) == ["symbols"]
    untagged = b.TagMap(units={"unit_m3": ["symbols", "wiring", "diagrams"]})
    assert untagged.tags_for(quiz, quiz.question("q_01")) == ["symbols", "wiring", "diagrams"]


def test_events_carry_type_partial_credit_and_attempt(quiz):
    events = b.attempt_events(quiz, b.parse_attempt(attempts()[0]), b.TagMap.load())
    assert [e.question_type for e in events] == ["multiple_choice", "multiple_choice", "true_false", "multiple_choice", "short_answer"]
    assert events[-1].score == pytest.approx(4 / 20) and events[0].score is None
    assert all(e.attempt_number == 1 for e in events)


def test_unmarked_short_answers_are_left_out(quiz):
    events = b.attempt_events(quiz, b.parse_attempt(attempts()[2]), b.TagMap.load())
    assert len(events) == 4 and all(e.question_type != "short_answer" for e in events)
    assert all(e.attempt_number == 2 for e in events)


def test_unit_tags_from_our_modules_cover_every_module():
    tags = b.TagMap.from_modules()
    assert tags.problems() == [] and tags.units["unit_m3"] == ["symbols", "wiring", "diagrams"]


def test_the_default_tag_file_has_only_known_concepts():
    assert b.TagMap.load().problems() == []


# ---- the adapter endpoint ------------------------------------------------------------------


@pytest.fixture
def client():
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from circuit_coach.api import app

    return TestClient(app)


def test_endpoint_diagnoses_a_barabari_attempt(client):
    r = client.post("/v1/barabari/quiz-attempt", json={"state": {}, "quiz": quiz_dict(), "attempt": attempts()[1], "now": 9})
    assert r.status_code == 200
    body = r.json()
    assert body["score"]["passed"] is False and body["score"]["percent"] == 52.0
    assert body["recommendation"]["concept_id"] == "symbols"
    assert body["recommendation"]["chain"] == ["diagrams", "symbols"]
    assert body["assessed_concepts"] == ["safety", "symbols", "wiring", "diagrams"]
    assert body["state"]["observations"]["diagrams"] == 2


def test_endpoint_gives_no_lesson_for_a_clean_attempt(client):
    body = client.post("/v1/barabari/quiz-attempt", json={"state": {}, "quiz": quiz_dict(), "attempt": attempts()[3]}).json()
    assert body["recommendation"] is None and body["score"]["passed"] is True


def test_endpoint_accepts_custom_tags(client):
    tags = {"units": {"unit_m3": ["wiring"]}}
    body = client.post("/v1/barabari/quiz-attempt", json={"state": {}, "quiz": quiz_dict(), "attempt": attempts()[0], "tags": tags}).json()
    assert body["assessed_concepts"] == ["wiring"] and set(body["state"]["observations"]) == {"wiring"}


@pytest.mark.parametrize(
    "change",
    [
        lambda q, a: a.update(quiz_id="other_quiz"),
        lambda q, a: a["answers"].append({"question_id": "q_99", "selected_option_id": "x"}),
        lambda q, a: q["questions"][0]["options"][1].update(is_correct=True),
        lambda q, a: (q.update(id="quiz_untagged", unit_id="unit_unknown"), a.update(quiz_id="quiz_untagged")),
        lambda q, a: a["answers"].append(dict(a["answers"][0])),
    ],
)
def test_endpoint_rejects_inconsistent_input(client, change):
    q, a = copy.deepcopy(quiz_dict()), copy.deepcopy(attempts()[0])
    change(q, a)
    assert client.post("/v1/barabari/quiz-attempt", json={"state": {}, "quiz": q, "attempt": a}).status_code == 422


def test_quiz_result_accepts_the_new_event_fields(client):
    events = [
        {"concept_tags": ["wiring"], "is_correct": True, "question_type": "true_false"},
        {"concept_tags": ["diagrams"], "is_correct": False, "question_type": "short_answer", "score": 0.3, "attempt_number": 2},
    ]
    assert client.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": events}).status_code == 200
    bad = [{"concept_tags": ["wiring"], "is_correct": True, "score": 1.5}]
    assert client.post("/v1/quiz-result", json={"state": {}, "module_id": "m3", "events": bad}).status_code == 422
