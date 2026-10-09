"""Knowledge tracing and recommendation engine (Design Doc section 5).

Behaviour ported from the in-browser prototype (`frontend/src/engine/engine.ts`):

1. Update a mastery probability per concept after every response (BKT, one model per concept).
   A question tagged with several concepts updates each of them (naive credit assignment).
2. Find the root cause: from the weakest concept just assessed, walk back through the
   concept graph to the weakest prerequisite that is also below the gap threshold.
3. Resolve to exactly one lesson, skipping any the learner has already tried.

The learner state is plain data (`mastery`, `observations`, `tried`) so the service can stay
stateless: the caller sends the state and gets the updated state back.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from . import bkt
from .bkt import BKTParams
from .curriculum import CONCEPTS, CONTENT, MODULES

STRONG = 0.8  # at or above: strong
WEAK = 0.6  # below: a gap

_PARAMS_FILE = Path(__file__).with_name("fitted_params.json")


def load_params(path: Path | None = None) -> dict[str, BKTParams]:
    """Per-concept parameters: fitted values if `fitted_params.json` exists, else hand-set."""
    path = path or _PARAMS_FILE
    params = {c: bkt.HAND_SET for c in CONCEPTS}
    if path.exists():
        raw = json.loads(path.read_text())
        for c, d in raw.get("concepts", {}).items():
            if c in params:
                params[c] = BKTParams.from_dict(d)
    return params


@dataclass
class LearnerState:
    mastery: dict[str, float] = field(default_factory=dict)
    observations: dict[str, int] = field(default_factory=dict)
    tried: dict[str, list[str]] = field(default_factory=dict)

    def copy(self) -> "LearnerState":
        return LearnerState(dict(self.mastery), dict(self.observations), {k: list(v) for k, v in self.tried.items()})


@dataclass(frozen=True)
class Event:
    concept_tags: tuple[str, ...]
    is_correct: bool
    unsure: bool = False


class Engine:
    def __init__(self, params: dict[str, BKTParams] | None = None, use_prerequisites: bool = True):
        self.params = params or load_params()
        # Switching this off gives the "no root-cause walk" variant used in the evaluation.
        self.use_prerequisites = use_prerequisites

    # ---- tracing ---------------------------------------------------------------------

    def mastery_of(self, state: LearnerState, concept: str) -> float:
        return state.mastery.get(concept, self.params[concept].p_init)

    def trace(self, state: LearnerState, events: Iterable[Event]) -> LearnerState:
        """Return a new state after observing the events in order."""
        out = state.copy()
        for ev in events:
            for c in ev.concept_tags:
                if c not in self.params:
                    continue
                out.mastery[c] = bkt.update(self.mastery_of(out, c), ev.is_correct, self.params[c], ev.unsure)
                out.observations[c] = out.observations.get(c, 0) + 1
        return out

    def got_it(self, state: LearnerState, concept: str) -> LearnerState:
        """The learner says "Got it!": apply a learning step, but do not trust it as proof."""
        out = state.copy()
        out.mastery[concept] = bkt.learn_step(self.mastery_of(out, concept), self.params[concept])
        return out

    def onboarding_prior(self, experience: str) -> float:
        base = {"new": 0.12, "experienced": 0.45}.get(experience)
        return base if base is not None else 0.30

    def onboard(self, experience: str, events: Iterable[Event]) -> tuple[LearnerState, str]:
        prior = self.onboarding_prior(experience)
        state = LearnerState(mastery={c: prior for c in CONCEPTS})
        state = self.trace(state, events)
        return state, self.start_module(state)

    def start_module(self, state: LearnerState) -> str:
        """First module with an unobserved or weak concept."""
        for mid, m in MODULES.items():
            if any(not state.observations.get(c) or self.mastery_of(state, c) < WEAK for c in m["concepts"]):
                return mid
        return next(iter(MODULES))

    # ---- recommendation ----------------------------------------------------------------

    def root_cause(self, state: LearnerState, concept: str, seen: set[str] | None = None) -> list[str]:
        """Chain from `concept` back to the deepest weak prerequisite blocking it."""
        seen = seen if seen is not None else set()
        seen.add(concept)
        if not self.use_prerequisites:
            return [concept]
        weak = [
            p
            for p in CONCEPTS[concept]["prereqs"]
            if p not in seen and self.mastery_of(state, p) < WEAK and state.observations.get(p, 0) > 0
        ]
        weak.sort(key=lambda p: self.mastery_of(state, p))
        if not weak:
            return [concept]
        return [concept, *self.root_cause(state, weak[0], seen)]

    def observed_gap(self, state: LearnerState, assessed: list[str]) -> str | None:
        """The most advanced weak concept just assessed (deepest in the graph, then weakest)."""
        gaps = [c for c in assessed if self.mastery_of(state, c) < WEAK]
        if not gaps:
            return None
        gaps.sort(key=lambda c: (-CONCEPTS[c]["col"], self.mastery_of(state, c)))
        return gaps[0]

    def pick_content(self, state: LearnerState, concept: str) -> str:
        items = CONTENT[concept]
        tried = state.tried.get(concept, [])
        return next((i for i in items if i not in tried), items[0])

    def recommend(self, state: LearnerState, assessed: list[str], now_ms: int = 0, repeat: bool = False) -> dict | None:
        observed = self.observed_gap(state, assessed)
        if observed is None:
            return None
        chain = self.root_cause(state, observed)
        target = chain[-1]
        strong_pool = [c for c in assessed if c != observed and c not in chain and self.mastery_of(state, c) >= WEAK]
        strong = max(strong_pool, key=lambda c: self.mastery_of(state, c)) if strong_pool else None
        return {
            "concept_id": target,
            "observed_concept_id": observed,
            "chain": chain,
            "strong_concept_id": strong,
            "diagnostic_text": diagnostic(observed, target, strong, repeat),
            "recommended_content_id": self.pick_content(state, target),
            "repeat_gap": repeat,
            "created_at": now_ms,
        }

    def recommend_repeat(self, state: LearnerState, concept: str, now_ms: int = 0) -> dict:
        """The learner said "Got it!" but failed the follow-up check: try again, differently."""
        rec = self.recommend(state, [concept], now_ms, repeat=True)
        if rec is not None:
            return rec
        return {
            "concept_id": concept,
            "observed_concept_id": concept,
            "chain": [concept],
            "strong_concept_id": None,
            "diagnostic_text": diagnostic(concept, concept, None, True),
            "recommended_content_id": self.pick_content(state, concept),
            "repeat_gap": True,
            "created_at": now_ms,
        }


# ---- plain-language diagnostic (same copy as the prototype) --------------------------


def _lower(s: str) -> str:
    return s[:1].lower() + s[1:]


def diagnostic(observed: str, target: str, strong: str | None, repeat: bool) -> dict[str, str]:
    n = {c: CONCEPTS[c] for c in (observed, target, *([strong] if strong else []))}
    t_en, t_hi = _lower(n[target]["en"]), n[target]["hi"]
    if repeat:
        return {
            "en": f"Let's go over {t_en} again, a different way this time.",
            "hi": f"चलिए {t_hi} को फिर से देखते हैं, इस बार नए तरीके से।",
        }
    if observed != target:
        return {
            "en": f"You got stuck on {_lower(n[observed]['en'])}. It builds on {t_en}, so let's start there.",
            "hi": f"आप {n[observed]['hi']} में अटके। यह {t_hi} पर टिका है, इसलिए वहीं से शुरू करते हैं।",
        }
    if strong:
        return {
            "en": f"You did well on {_lower(n[strong]['en'])}. Now let's take a closer look at {t_en}.",
            "hi": f"{n[strong]['hi']} में आपने अच्छा किया। अब {t_hi} को ध्यान से देखते हैं।",
        }
    return {"en": f"Let's take a closer look at {t_en}.", "hi": f"चलिए {t_hi} को ध्यान से देखते हैं।"}


def band(state: LearnerState, engine: Engine, concept: str) -> str:
    if not state.observations.get(concept):
        return "new"
    p = engine.mastery_of(state, concept)
    return "strong" if p >= STRONG else "getting" if p >= WEAK else "practice"
