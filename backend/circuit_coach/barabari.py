"""Barabari Collective's quiz format (Async-LMS), read into engine events.

Barabari attaches a quiz to each unit (`quizzes.unit_id`). A question is `multiple_choice`
(2 to 6 options, one correct), `true_false`, or `short_answer` (graded by an instructor), and
carries its own `points`. A quiz passes at `passing_score` out of `max_score` (60% by default).
Students can retake a quiz; every attempt is kept in `quiz_attempts`, and correct answers are
revealed only after 3 attempts.

What this module does:

* `parse_quiz` reads a quiz in Barabari's JSON shape and `validate_quiz` checks it.
* `attempt_events` turns one attempt into engine events: the question type sets the chance of a
  lucky guess, points earned on a short answer become partial credit, and the attempt number
  makes retakes count for less.
* Barabari's data has no concept tags, so `TagMap` tags every question with its unit's
  concepts (the fallback agreed in PLAN.md). A trainer can override any question with its own
  tags, and question-level tags always win.

Barabari has not shared the `quiz_attempts` columns yet. `parse_attempt` reads the shape we
assume until they do (documented in `docs/barabari_format.md`); only that function would change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .bkt import QUESTION_TYPES
from .curriculum import CONCEPTS, MODULES
from .engine import Event

MIN_ATTEMPTS_FOR_REVEAL = 3
DEFAULT_PASS_SHARE = 0.6
DEFAULT_TAGS_FILE = Path(__file__).with_name("barabari_tags.json")


@dataclass(frozen=True)
class Option:
    id: str
    option_text: str
    is_correct: bool


@dataclass(frozen=True)
class Question:
    id: str
    question_text: str
    question_type: str
    points: float
    explanation: str = ""
    options: tuple[Option, ...] = ()


@dataclass(frozen=True)
class Quiz:
    id: str
    unit_id: str
    title: str
    passing_score: float
    max_score: float
    questions: tuple[Question, ...]

    def question(self, qid: str) -> Question | None:
        return next((q for q in self.questions if q.id == qid), None)


@dataclass(frozen=True)
class Answer:
    question_id: str
    selected_option_id: str | None = None
    text_answer: str | None = None
    points_earned: float | None = None  # set by the instructor for a short answer


@dataclass(frozen=True)
class Attempt:
    id: str
    quiz_id: str
    student_id: str
    attempt_number: int
    answers: tuple[Answer, ...]
    submitted_at: str | None = None


@dataclass
class TagMap:
    """Concept tags for Barabari questions: per unit, with per-question overrides."""

    units: dict[str, list[str]] = field(default_factory=dict)
    questions: dict[str, list[str]] = field(default_factory=dict)

    def tags_for(self, quiz: Quiz, question: Question) -> list[str]:
        return self.questions.get(f"{quiz.id}/{question.id}") or self.questions.get(question.id) or self.units.get(quiz.unit_id, [])

    def problems(self) -> list[str]:
        out = []
        for where, table in (("unit", self.units), ("question", self.questions)):
            for key, tags in table.items():
                unknown = set(tags) - set(CONCEPTS)
                if unknown:
                    out.append(f"{where} {key}: unknown concepts {sorted(unknown)}")
        return out

    @staticmethod
    def from_dict(d: dict) -> "TagMap":
        return TagMap({k: list(v) for k, v in d.get("units", {}).items()}, {k: list(v) for k, v in d.get("questions", {}).items()})

    @staticmethod
    def load(path: Path | None = None) -> "TagMap":
        return TagMap.from_dict(json.loads((path or DEFAULT_TAGS_FILE).read_text(encoding="utf8")))

    @staticmethod
    def from_modules() -> "TagMap":
        """Unit `unit_<module id>` carries that module's concepts (our own course as Barabari units)."""
        return TagMap({f"unit_{mid}": list(m["concepts"]) for mid, m in MODULES.items()})


# ---- reading -------------------------------------------------------------------------------


def parse_quiz(d: dict) -> Quiz:
    return Quiz(
        id=str(d["id"]),
        unit_id=str(d["unit_id"]),
        title=str(d.get("title", "")),
        passing_score=float(d.get("passing_score", DEFAULT_PASS_SHARE * float(d.get("max_score", 100)))),
        max_score=float(d.get("max_score", 100)),
        questions=tuple(
            Question(
                id=str(q["id"]),
                question_text=str(q.get("question_text", "")),
                question_type=str(q["question_type"]),
                points=float(q.get("points", 1)),
                explanation=str(q.get("explanation", "")),
                options=tuple(Option(str(o["id"]), str(o.get("option_text", "")), bool(o.get("is_correct", False))) for o in q.get("options", [])),
            )
            for q in d.get("questions", [])
        ),
    )


def parse_attempt(d: dict) -> Attempt:
    return Attempt(
        id=str(d["id"]),
        quiz_id=str(d["quiz_id"]),
        student_id=str(d["student_id"]),
        attempt_number=int(d.get("attempt_number", 1)),
        submitted_at=d.get("submitted_at"),
        answers=tuple(
            Answer(str(a["question_id"]), a.get("selected_option_id"), a.get("text_answer"), a.get("points_earned"))
            for a in d.get("answers", [])
        ),
    )


def validate_quiz(quiz: Quiz) -> list[str]:
    """Problems with a quiz under Barabari's rules (empty when it is well formed)."""
    out = []
    if not 0 < quiz.passing_score <= quiz.max_score:
        out.append(f"{quiz.id}: passing_score must be above 0 and at most max_score")
    ids = [q.id for q in quiz.questions]
    if len(set(ids)) != len(ids):
        out.append(f"{quiz.id}: duplicate question ids")
    for q in quiz.questions:
        where = f"{quiz.id}/{q.id}"
        if q.question_type not in QUESTION_TYPES:
            out.append(f"{where}: unknown question_type {q.question_type!r}")
            continue
        if q.points <= 0:
            out.append(f"{where}: points must be positive")
        right = sum(o.is_correct for o in q.options)
        if q.question_type == "multiple_choice" and not (2 <= len(q.options) <= 6 and right == 1):
            out.append(f"{where}: multiple_choice needs 2 to 6 options and exactly one correct")
        if q.question_type == "true_false" and not (len(q.options) == 2 and right == 1):
            out.append(f"{where}: true_false needs two options (True, False) and one correct")
        if q.question_type == "short_answer" and q.options:
            out.append(f"{where}: short_answer takes no options")
    return out


# ---- grading and events --------------------------------------------------------------------


def grade(question: Question, answer: Answer) -> float | None:
    """Fraction of the question's points earned, or None while a short answer awaits review."""
    if question.question_type == "short_answer":
        if answer.points_earned is None:
            return None
        return min(1.0, max(0.0, float(answer.points_earned) / question.points))
    chosen = next((o for o in question.options if o.id == answer.selected_option_id), None)
    return 1.0 if chosen is not None and chosen.is_correct else 0.0


def attempt_score(quiz: Quiz, attempt: Attempt) -> dict:
    """Barabari's own result for an attempt: points, percentage and pass or fail."""
    earned = pending = 0.0
    for a in attempt.answers:
        q = quiz.question(a.question_id)
        if q is None:
            continue
        g = grade(q, a)
        if g is None:
            pending += q.points
        else:
            earned += g * q.points
    total = sum(q.points for q in quiz.questions) or quiz.max_score
    scaled = earned / total * quiz.max_score
    return {
        "points": round(scaled, 2),
        "max_score": quiz.max_score,
        "percent": round(100 * scaled / quiz.max_score, 1),
        "passed": scaled >= quiz.passing_score,
        "awaiting_review_points": pending,
        "answers_revealed": attempt.attempt_number >= MIN_ATTEMPTS_FOR_REVEAL,
    }


def attempt_events(quiz: Quiz, attempt: Attempt, tags: TagMap) -> list[Event]:
    """Engine events for one attempt, in answer order. Ungraded short answers are skipped."""
    out = []
    for a in attempt.answers:
        q = quiz.question(a.question_id)
        concepts = [c for c in tags.tags_for(quiz, q)] if q else []
        if q is None or not concepts:
            continue
        g = grade(q, a)
        if g is None:
            continue
        partial = q.question_type == "short_answer"
        out.append(
            Event(
                concept_tags=tuple(concepts),
                is_correct=g >= 0.5,
                question_type=q.question_type,
                score=g if partial else None,
                attempt_number=attempt.attempt_number,
            )
        )
    return out


def quiz_concepts(quiz: Quiz, tags: TagMap) -> list[str]:
    """The concepts a quiz assesses, in curriculum order."""
    seen = {c for q in quiz.questions for c in tags.tags_for(quiz, q)}
    return [c for c in CONCEPTS if c in seen]
