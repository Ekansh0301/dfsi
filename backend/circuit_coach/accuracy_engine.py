"""A simpler engine for comparison: mastery is the learner's smoothed accuracy so far.

Used only in the evaluation (scripts/accuracy_baseline.py), never by the service. It keeps every
other part of the engine (the 0.6 threshold, the prerequisite walk, lesson choice), so comparing
it with BKT isolates what knowledge tracing adds over "percent correct below the pass mark".

Mastery of a concept after n answers with k right is (k + 1) / (n + 2): one right answer gives
0.67, one wrong answer 0.33, one of each 0.5. Every tag on a question gets the credit, "I'm not
sure" counts as wrong, a short answer counts its partial credit, and old answers never fade.
"""

from __future__ import annotations

from collections.abc import Iterable

from . import bkt
from .curriculum import CONCEPTS
from .engine import BASELINE, Engine, Event, LearnerState, ModelOptions


class AccuracyEngine(Engine):
    def __init__(self, options: ModelOptions = BASELINE):
        super().__init__({c: bkt.HAND_SET for c in CONCEPTS}, use_prerequisites=True, options=options)

    def mastery_of(self, state: LearnerState, concept: str) -> float:
        return state.mastery.get(concept, 0.5)

    def trace(self, state: LearnerState, events: Iterable[Event]) -> LearnerState:
        out = state.copy()
        # Recover the counts from the state, so tracing can continue from any earlier state.
        n = {c: out.observations.get(c, 0) for c in CONCEPTS}
        k = {c: out.mastery.get(c, 0.5) * (n[c] + 2) - 1 for c in CONCEPTS}
        for ev in events:
            credit = ev.score if ev.score is not None else float(ev.is_correct and not ev.unsure)
            for c in dict.fromkeys(ev.concept_tags):
                if c not in CONCEPTS:
                    continue
                n[c] += 1
                k[c] += credit
                out.mastery[c] = (k[c] + 1) / (n[c] + 2)
                out.observations[c] = n[c]
        return out

    def got_it(self, state: LearnerState, concept: str) -> LearnerState:
        return state.copy()
