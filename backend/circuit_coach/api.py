"""HTTP service for the knowledge tracing engine.

The service is stateless: every request carries the learner's current model state
(`mastery`, `observations`, `tried`) and the response carries the updated state. Storing
learners is a separate concern (planned for Sprint 3), and this keeps the engine easy to
test and to call from the prototype.

Run:  uvicorn circuit_coach.api:app --port 8000
"""

from __future__ import annotations

import hmac
import math
import os
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import __version__, barabari
from .storage import KeyReused, Storage
from .curriculum import CONCEPTS, CONTENT, MODULES
from .engine import _PARAMS_FILE, MODELS, Engine, Event, LearnerState, load_params

app = FastAPI(title="Circuit Coach engine", version=__version__)

# Browsers may call the service only from these sites (comma-separated; "*" allows any).
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,https://dfsi.vercel.app"
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()]

# Optional shared key: when CIRCUIT_COACH_API_KEY is set, every /v1/ call must send it in the
# X-API-Key header (for server-to-server use, such as Barabari's LMS). /health and /docs stay open.
API_KEY: str | None = os.environ.get("CIRCUIT_COACH_API_KEY") or None


@app.middleware("http")
async def require_api_key(request: Request, call_next):
    if API_KEY and request.url.path.startswith("/v1/") and request.method != "OPTIONS":
        sent = request.headers.get("x-api-key", "")
        if not hmac.compare_digest(sent.encode(), API_KEY.encode()):
            return JSONResponse(status_code=401, content={"detail": "Missing or wrong X-API-Key header"})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Request size limits: far above any real quiz, low enough that one request cannot tie up the service.
MAX_EVENTS = 500
MAX_TAGS = 10
MAX_TRIED = 50
MAX_QUESTIONS = 500
ModelName = Literal["baseline", "improved"]
# The service default is the improved model (promoted in Hackathon 2 after the EdNet check, see
# docs/evaluation.md). The baseline stays selectable per request (?model=baseline) and through
# this setting (CIRCUIT_COACH_MODEL=baseline).
DEFAULT_MODEL: str = os.environ.get("CIRCUIT_COACH_MODEL", "improved")
if DEFAULT_MODEL not in MODELS:
    raise RuntimeError(f"CIRCUIT_COACH_MODEL must be one of {sorted(MODELS)}")
engines = {name: Engine(load_params(model=name), options=opt) for name, opt in MODELS.items()}
engine = engines[DEFAULT_MODEL]


def _json_safe(x):
    """NaN and infinity cannot be written as JSON; echo them back as text."""
    if isinstance(x, float) and not math.isfinite(x):
        return str(x)
    if isinstance(x, dict):
        return {k: _json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_safe(v) for v in x]
    return x


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    """A 422 even when the bad input itself is not valid JSON (for example NaN), never a 500 (S4-1)."""
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(_json_safe(list(exc.errors())))})


def pick(model: str | None) -> Engine:
    return engines[model or DEFAULT_MODEL]


# Optional storage (PLAN S4-4): set CIRCUIT_COACH_DB to a database URL to keep learner state.
store: Storage | None = Storage.from_env()
LEARNER_ID = Field(default=None, max_length=128, description="With storage on: load this learner's saved state when `state` is empty, and save the result")


def start_state(req) -> LearnerState:
    """The request's state, or the learner's stored state when the request sends none."""
    state = req.state.to_state() if hasattr(req, "state") else LearnerState()
    learner_id = getattr(req, "learner_id", None)
    if store and learner_id and not (state.mastery or state.observations or state.tried):
        return store.load(learner_id) or state
    return state


REQUEST_ID = Field(default=None, max_length=128, description="With storage on: a resent request with the same id for the same learner returns the saved response instead of being applied twice")


def request_key(req) -> str | None:
    return getattr(req, "request_id", None)


def replay(req, step: str) -> dict | None:
    """The saved response if this request was already applied (storage on, same learner and key)."""
    learner_id, key = getattr(req, "learner_id", None), request_key(req)
    if store and learner_id and key:
        try:
            return store.replay(learner_id, step, key, req.model_dump(mode="json"))
        except KeyReused:
            raise HTTPException(409, f"request_id {key} was already used for a different {step} request")
    return None


def remember(req, step: str, model: str | None, state: LearnerState, rec: dict | None, response: BaseModel):
    """Save the state and log the step (storage on). Returns the response to send: the new one,
    or the saved one if an identical request was applied a moment earlier."""
    learner_id = getattr(req, "learner_id", None)
    if store and learner_id:
        try:
            earlier = store.record(
                learner_id, state, step, model or DEFAULT_MODEL, req.model_dump(mode="json"), rec, request_key(req), response.model_dump(mode="json")
            )
        except KeyReused:
            raise HTTPException(409, f"request_id {request_key(req)} was already used for a different {step} request")
        if earlier is not None:
            return earlier
    return response


MODEL_QUERY = Query(default=None, description="Engine model for this request: baseline or improved. Defaults to the service setting")


Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Count = Annotated[int, Field(ge=0)]


class StateModel(BaseModel):
    mastery: dict[str, Probability] = Field(default_factory=dict, description="P(concept mastered), 0 to 1")
    observations: dict[str, Count] = Field(default_factory=dict, description="Answers seen per concept")
    tried: dict[str, Annotated[list[Annotated[str, Field(max_length=64)]], Field(max_length=MAX_TRIED)]] = Field(
        default_factory=dict, description="Lessons already tried per concept"
    )

    def to_state(self) -> LearnerState:
        unknown = (set(self.mastery) | set(self.observations) | set(self.tried)) - set(CONCEPTS)
        if unknown:
            raise HTTPException(422, f"Unknown concepts: {sorted(unknown)}")
        return LearnerState(dict(self.mastery), dict(self.observations), {k: list(v) for k, v in self.tried.items()})

    @staticmethod
    def of(state: LearnerState) -> "StateModel":
        return StateModel(mastery=state.mastery, observations=state.observations, tried=state.tried)


class EventModel(BaseModel):
    concept_tags: list[str] = Field(min_length=1, max_length=MAX_TAGS)
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
    events: list[EventModel] = Field(default_factory=list, max_length=MAX_EVENTS)
    learner_id: str | None = LEARNER_ID
    request_id: str | None = REQUEST_ID


class OnboardingResponse(BaseModel):
    state: StateModel
    start_module_id: str


class QuizResultRequest(BaseModel):
    state: StateModel
    module_id: str
    events: list[EventModel] = Field(max_length=MAX_EVENTS)
    recheck_concept: str | None = Field(default=None, description="Set when a spaced re-check was answered wrongly")
    now: int = Field(default=0, description="Timestamp (ms) stored on the recommendation")
    learner_id: str | None = LEARNER_ID
    request_id: str | None = REQUEST_ID


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
    content_id: str | None = Field(
        default=None, description="The lesson the learner just finished; it is added to `tried` so a repeat gap gets a different one"
    )
    learner_id: str | None = LEARNER_ID
    request_id: str | None = REQUEST_ID


class GotItResponse(BaseModel):
    state: StateModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    parameters: Literal["fitted", "hand-set"]
    model: ModelName = Field(description="The model used when a request does not choose one")
    models: list[ModelName]


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
    return {
        "status": "ok",
        "version": __version__,
        "parameters": "fitted" if _PARAMS_FILE.exists() else "hand-set",
        "model": DEFAULT_MODEL,
        "models": sorted(MODELS),
    }


@app.get("/v1/concepts", response_model=ConceptsResponse)
def concepts() -> dict:
    """The concept graph, modules and lessons the engine knows about."""
    return {
        "concepts": {c: {"name": {"en": d["en"], "hi": d["hi"]}, "prereqs": d["prereqs"]} for c, d in CONCEPTS.items()},
        "modules": MODULES,
        "content": CONTENT,
    }


@app.post("/v1/onboarding", response_model=OnboardingResponse)
def onboarding(req: OnboardingRequest, model: ModelName | None = MODEL_QUERY) -> OnboardingResponse:
    """Seed a new learner's model from their stated experience and the placement quiz."""
    engine = pick(model)
    if (hit := replay(req, "onboarding")) is not None:
        return hit
    state, start = engine.onboard(req.experience, [e.to_event() for e in req.events])
    out = OnboardingResponse(state=StateModel.of(state), start_module_id=start)
    return remember(req, "onboarding", model, state, None, out)


@app.post("/v1/quiz-result", response_model=QuizResultResponse)
def quiz_result(req: QuizResultRequest, model: ModelName | None = MODEL_QUERY) -> QuizResultResponse:
    """Update the model from a finished quick check and return the single recommendation.

    When `recheck_concept` is set (a spaced re-check was failed) the recommendation is marked
    as a repeat gap and uses a lesson the learner has not tried.
    """
    if req.module_id not in MODULES:
        raise HTTPException(404, f"Unknown module {req.module_id}")
    if (hit := replay(req, "quiz-result")) is not None:
        return hit
    engine = pick(model)
    state = engine.trace(start_state(req), [e.to_event() for e in req.events])
    if req.recheck_concept:
        if req.recheck_concept not in CONCEPTS:
            raise HTTPException(422, f"Unknown concept {req.recheck_concept}")
        rec = engine.recommend_repeat(state, req.recheck_concept, req.now)
    else:
        rec = engine.recommend(state, MODULES[req.module_id]["concepts"], req.now)
    out = QuizResultResponse(state=StateModel.of(state), recommendation=rec)
    return remember(req, "quiz-result", model, state, rec, out)


@app.post("/v1/got-it", response_model=GotItResponse)
def got_it(req: GotItRequest, model: ModelName | None = MODEL_QUERY) -> GotItResponse:
    """The learner said "Got it!": apply a learning step. Mastery is confirmed by a later re-check."""
    if req.concept_id not in CONCEPTS:
        raise HTTPException(422, f"Unknown concept {req.concept_id}")
    if req.content_id is not None and req.content_id not in CONTENT[req.concept_id]:
        raise HTTPException(422, f"Unknown lesson {req.content_id} for {req.concept_id}")
    if (hit := replay(req, "got-it")) is not None:
        return hit
    engine = pick(model)
    state = engine.got_it(start_state(req), req.concept_id)
    if req.content_id is not None:
        done = state.tried.setdefault(req.concept_id, [])
        if req.content_id not in done:
            done.append(req.content_id)
    out = GotItResponse(state=StateModel.of(state))
    return remember(req, "got-it", model, state, None, out)



class MarkedAnswerRequest(BaseModel):
    state: StateModel
    concept_tags: list[str] = Field(min_length=1, max_length=MAX_TAGS)
    score: float = Field(ge=0, le=1, description="The trainer's mark as a share of the question's points")
    attempt_number: int = Field(default=1, ge=1)
    now: int = 0
    learner_id: str | None = LEARNER_ID
    request_id: str | None = REQUEST_ID


@app.post("/v1/marked-answer", response_model=QuizResultResponse)
def marked_answer(req: MarkedAnswerRequest, model: ModelName | None = MODEL_QUERY) -> QuizResultResponse:
    """A trainer marked a short answer: trace it as partial credit and recheck its concepts.

    Short answers wait for a trainer, so they reach the model after the quick check. The
    recommendation covers only the marked answer's concepts (null when they look fine).
    """
    ev = EventModel(concept_tags=req.concept_tags, is_correct=req.score >= 0.5, question_type="short_answer", score=req.score, attempt_number=req.attempt_number)
    if (hit := replay(req, "marked-answer")) is not None:
        return hit
    engine = pick(model)
    state = engine.trace(start_state(req), [ev.to_event()])
    rec = engine.recommend(state, [c for c in CONCEPTS if c in req.concept_tags], req.now)
    out = QuizResultResponse(state=StateModel.of(state), recommendation=rec)
    return remember(req, "marked-answer", model, state, rec, out)

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
    questions: list[BarabariQuestion] = Field(min_length=1, max_length=MAX_QUESTIONS)


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
    answers: list[BarabariAnswer] = Field(max_length=MAX_QUESTIONS)


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
    learner_id: str | None = Field(default=None, max_length=128, description="Defaults to the attempt's student_id when storage is on")
    request_id: str | None = Field(default=None, max_length=128, description="Defaults to the attempt id: the same attempt sent twice is applied once")


class BarabariAttemptResponse(BaseModel):
    state: StateModel
    recommendation: RecommendationModel | None
    score: BarabariScore
    assessed_concepts: list[str]


@app.post("/v1/barabari/quiz-attempt", response_model=BarabariAttemptResponse)
def barabari_quiz_attempt(req: BarabariAttemptRequest, model: ModelName | None = MODEL_QUERY) -> BarabariAttemptResponse:
    """Trace one attempt from Barabari's LMS and return the recommendation and the quiz score."""
    quiz = barabari.parse_quiz(req.quiz.model_dump())
    attempt = barabari.parse_attempt(req.attempt.model_dump())
    problems = barabari.validate_quiz(quiz)
    if attempt.quiz_id != quiz.id:
        problems.append(f"attempt is for quiz {attempt.quiz_id}, not {quiz.id}")
    unknown = sorted({a.question_id for a in attempt.answers} - {q.id for q in quiz.questions})
    if unknown:
        problems.append(f"answers to unknown questions {unknown}")
    answered = [a.question_id for a in attempt.answers]
    repeated = sorted({q for q in answered if answered.count(q) > 1})
    if repeated:
        problems.append(f"more than one answer to questions {repeated}")
    tags = barabari.TagMap.from_dict(req.tags.model_dump()) if req.tags else barabari.TagMap.load()
    problems += tags.problems()
    if problems:
        raise HTTPException(422, problems)
    assessed = barabari.quiz_concepts(quiz, tags)
    if not assessed:
        raise HTTPException(422, f"No concept tags for unit {quiz.unit_id}; add it to the tag map")
    engine = pick(model)
    if req.learner_id is None:
        req.learner_id = attempt.student_id
    if req.request_id is None:
        req.request_id = f"attempt:{attempt.id}"
    if (hit := replay(req, "barabari-quiz-attempt")) is not None:
        return hit
    state = engine.trace(start_state(req), barabari.attempt_events(quiz, attempt, tags))
    rec = engine.recommend(state, assessed, req.now)
    out = BarabariAttemptResponse(
        state=StateModel.of(state), recommendation=rec, score=barabari.attempt_score(quiz, attempt), assessed_concepts=assessed
    )
    return remember(req, "barabari-quiz-attempt", model, state, rec, out)



@app.get("/v1/learners/{learner_id}/state", response_model=StateModel)
def learner_state(learner_id: str) -> StateModel:
    """A learner's saved state (storage must be on: CIRCUIT_COACH_DB)."""
    if store is None:
        raise HTTPException(404, "Storage is off: set CIRCUIT_COACH_DB to keep learner state")
    state = store.load(learner_id)
    if state is None:
        raise HTTPException(404, f"No saved state for learner {learner_id}")
    return StateModel.of(state)
