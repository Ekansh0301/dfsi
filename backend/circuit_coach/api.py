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

from . import __version__
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

    def to_event(self) -> Event:
        unknown = set(self.concept_tags) - set(CONCEPTS)
        if unknown:
            raise HTTPException(422, f"Unknown concepts: {sorted(unknown)}")
        return Event(tuple(self.concept_tags), self.is_correct, self.unsure)


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


class QuizResultResponse(BaseModel):
    state: StateModel
    recommendation: dict | None


class GotItRequest(BaseModel):
    state: StateModel
    concept_id: str


class GotItResponse(BaseModel):
    state: StateModel


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "parameters": "fitted" if _PARAMS_FILE.exists() else "hand-set"}


@app.get("/v1/concepts")
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
