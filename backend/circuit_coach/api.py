"""HTTP service for the knowledge tracing engine.

The service is stateless: every request carries the learner's current model state
(`mastery`, `observations`, `tried`) and the response carries the updated state. Storing
learners is a separate concern (planned for Sprint 3), and this keeps the engine easy to
test and to call from the prototype.

Run:  uvicorn circuit_coach.api:app --port 8000
"""

from __future__ import annotations

import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import __version__, barabari
from .curriculum import CONCEPTS, CONTENT, MODULES
from .engine import _PARAMS_FILE, Engine, Event, LearnerState

app = FastAPI(title="Circuit Coach engine", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
engine = Engine()


class StateModel(BaseModel):
    mastery: dict[str, float] = Field(default_factory=dict, description="P(concept mastered), 0 to 1")
    observations: dict[str, int] = Field(default_factory=dict, description="Answers seen per concept")
    tried: dict[str, list[str]] = Field(default_factory=dict, description="Lessons already tried per concept")

    def to_state(self) -> LearnerState:
        unknown = (set(self.mastery) | set(self.observations) | set(self.tried)) - set(CONCEPTS)
        if unknown:
            raise HTTPException(422, f"Unknown concepts: {sorted(unknown)}")
        return LearnerState(dict(self.mastery), dict(self.observations), {k: list(v) for k, v in self.tried.items()})

    @staticmethod
    def of(state: LearnerState) -> "StateModel":
        return StateModel(mastery=state.mastery, observations=state.observations, tried=state.tried)


class EventModel(BaseModel):
    concept_tags: list[str] = Field(min_length=1)
    is_correct: bool
    unsure: bool = Field(default=False, description='The learner chose "I\'m not sure"')
    question_type: Literal["multiple_choice", "true_false", "short_answer"] = Field(
        default="multiple_choice", description="Barabari question type; sets the chance of a lucky guess"
    )
    score: float | None = Field(
        default=None, ge=0, le=1, description="Partial credit from 0 to 1 (points earned / points). Overrides is_correct"
    )
    attempt_number: int = Field(default=1, ge=1, description="1 for the first try at this quiz; retakes count for less")

    def to_event(self) -> Event:
        unknown = set(self.concept_tags) - set(CONCEPTS)
        if unknown:
            raise HTTPException(422, f"Unknown concepts: {sorted(unknown)}")
        return Event(tuple(self.concept_tags), self.is_correct, self.unsure, self.question_type, self.score, self.attempt_number)


class OnboardingRequest(BaseModel):
    experience: Literal["new", "some", "experienced"]
    events: list[EventModel] = Field(default_factory=list)


class OnboardingResponse(BaseModel):
    state: StateModel
    start_module_id: str


class QuizResultRequest(BaseModel):
    state: StateModel
    module_id: str
    events: list[EventModel]
    recheck_concept: str | None = Field(default=None, description="Set when a spaced re-check was answered wrongly")
    now: int = Field(default=0, description="Timestamp (ms) stored on the recommendation")


class TextModel(BaseModel):
    en: str
    hi: str


class RecommendationModel(BaseModel):
    concept_id: str = Field(description="The concept to work on (the root cause)")
    observed_concept_id: str = Field(description="The weak concept the quick check showed")
    chain: list[str] = Field(description="Walk from the observed concept back to the root cause")
    strong_concept_id: str | None = Field(description="A concept the learner did well on, for encouragement")
    diagnostic_text: TextModel
    recommended_content_id: str = Field(description="The one lesson to take next")
    repeat_gap: bool = Field(description="True when a follow-up check after \"Got it!\" was failed")
    created_at: int


class QuizResultResponse(BaseModel):
    state: StateModel
    recommendation: RecommendationModel | None = Field(description="Null when no gap was found")


class GotItRequest(BaseModel):
    state: StateModel
    concept_id: str


class GotItResponse(BaseModel):
    state: StateModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    parameters: Literal["fitted", "hand-set"]


class ConceptModel(BaseModel):
    name: TextModel
    prereqs: list[str]


class ModuleModel(BaseModel):
    number: int
    concepts: list[str]


class ConceptsResponse(BaseModel):
    concepts: dict[str, ConceptModel]
    modules: dict[str, ModuleModel]
    content: dict[str, list[str]] = Field(description="Lesson ids per concept, in recommendation order")


@app.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {"status": "ok", "version": __version__, "parameters": "fitted" if _PARAMS_FILE.exists() else "hand-set"}


@app.get("/v1/concepts", response_model=ConceptsResponse)
def concepts() -> dict:
    """The concept graph, modules and lessons the engine knows about."""
    return {
        "concepts": {c: {"name": {"en": d["en"], "hi": d["hi"]}, "prereqs": d["prereqs"]} for c, d in CONCEPTS.items()},
        "modules": MODULES,
        "content": CONTENT,
    }


@app.post("/v1/onboarding", response_model=OnboardingResponse)
def onboarding(req: OnboardingRequest) -> OnboardingResponse:
    """Seed a new learner's model from their stated experience and the placement quiz."""
    state, start = engine.onboard(req.experience, [e.to_event() for e in req.events])
    return OnboardingResponse(state=StateModel.of(state), start_module_id=start)


@app.post("/v1/quiz-result", response_model=QuizResultResponse)
def quiz_result(req: QuizResultRequest) -> QuizResultResponse:
    """Update the model from a finished quick check and return the single recommendation.

    When `recheck_concept` is set (a spaced re-check was failed) the recommendation is marked
    as a repeat gap and uses a lesson the learner has not tried.
    """
    if req.module_id not in MODULES:
        raise HTTPException(404, f"Unknown module {req.module_id}")
    state = engine.trace(req.state.to_state(), [e.to_event() for e in req.events])
    if req.recheck_concept:
        if req.recheck_concept not in CONCEPTS:
            raise HTTPException(422, f"Unknown concept {req.recheck_concept}")
        rec = engine.recommend_repeat(state, req.recheck_concept, req.now)
    else:
        rec = engine.recommend(state, MODULES[req.module_id]["concepts"], req.now)
    return QuizResultResponse(state=StateModel.of(state), recommendation=rec)


@app.post("/v1/got-it", response_model=GotItResponse)
def got_it(req: GotItRequest) -> GotItResponse:
    """The learner said "Got it!": apply a learning step. Mastery is confirmed by a later re-check."""
    if req.concept_id not in CONCEPTS:
        raise HTTPException(422, f"Unknown concept {req.concept_id}")
    return GotItResponse(state=StateModel.of(engine.got_it(req.state.to_state(), req.concept_id)))


# ---- Barabari adapter --------------------------------------------------------------------
# Barabari's LMS can send a quiz attempt in its own format; the service tags it with concepts,
# traces it and returns the same recommendation as /v1/quiz-result.


class BarabariOption(BaseModel):
    id: str
    option_text: str = ""
    is_correct: bool = False


class BarabariQuestion(BaseModel):
    id: str
    question_text: str = ""
    question_type: Literal["multiple_choice", "true_false", "short_answer"]
    points: float = Field(gt=0)
    explanation: str = ""
    options: list[BarabariOption] = Field(default_factory=list)


class BarabariQuiz(BaseModel):
    """A quiz as stored in Barabari's `quizzes` and `quiz_questions` tables."""

    id: str
    unit_id: str
    title: str = ""
    passing_score: float = 60
    max_score: float = 100
    questions: list[BarabariQuestion] = Field(min_length=1)


class BarabariAnswer(BaseModel):
    question_id: str
    selected_option_id: str | None = None
    text_answer: str | None = None
    points_earned: float | None = Field(default=None, ge=0, description="Instructor's mark for a short answer; null while awaiting review")


class BarabariAttempt(BaseModel):
    """One row of `quiz_attempts` (the shape we assume until Barabari shares theirs)."""

    id: str
    quiz_id: str
    student_id: str
    attempt_number: int = Field(default=1, ge=1)
    submitted_at: str | None = None
    answers: list[BarabariAnswer]


class BarabariTags(BaseModel):
    units: dict[str, list[str]] = Field(default_factory=dict, description="unit_id to concept ids")
    questions: dict[str, list[str]] = Field(default_factory=dict, description="question id (or quiz id/question id) to concept ids; wins over the unit")


class BarabariScore(BaseModel):
    points: float
    max_score: float
    percent: float
    passed: bool
    awaiting_review_points: float = Field(description="Points of short answers not marked yet; they are left out of the model")
    answers_revealed: bool = Field(description="True from the third attempt, when Barabari shows correct answers")


class BarabariAttemptRequest(BaseModel):
    state: StateModel
    quiz: BarabariQuiz
    attempt: BarabariAttempt
    tags: BarabariTags | None = Field(default=None, description="Concept tags; defaults to the service's barabari_tags.json")
    now: int = 0


class BarabariAttemptResponse(BaseModel):
    state: StateModel
    recommendation: RecommendationModel | None
    score: BarabariScore
    assessed_concepts: list[str]


@app.post("/v1/barabari/quiz-attempt", response_model=BarabariAttemptResponse)
def barabari_quiz_attempt(req: BarabariAttemptRequest) -> BarabariAttemptResponse:
    """Trace one attempt from Barabari's LMS and return the recommendation and the quiz score."""
    quiz = barabari.parse_quiz(req.quiz.model_dump())
    attempt = barabari.parse_attempt(req.attempt.model_dump())
    problems = barabari.validate_quiz(quiz)
    if attempt.quiz_id != quiz.id:
        problems.append(f"attempt is for quiz {attempt.quiz_id}, not {quiz.id}")
    unknown = sorted({a.question_id for a in attempt.answers} - {q.id for q in quiz.questions})
    if unknown:
        problems.append(f"answers to unknown questions {unknown}")
    tags = barabari.TagMap.from_dict(req.tags.model_dump()) if req.tags else barabari.TagMap.load()
    problems += tags.problems()
    if problems:
        raise HTTPException(422, problems)
    assessed = barabari.quiz_concepts(quiz, tags)
    if not assessed:
        raise HTTPException(422, f"No concept tags for unit {quiz.unit_id}; add it to the tag map")
    state = engine.trace(req.state.to_state(), barabari.attempt_events(quiz, attempt, tags))
    rec = engine.recommend(state, assessed, req.now)
    return BarabariAttemptResponse(
        state=StateModel.of(state), recommendation=rec, score=barabari.attempt_score(quiz, attempt), assessed_concepts=assessed
    )
