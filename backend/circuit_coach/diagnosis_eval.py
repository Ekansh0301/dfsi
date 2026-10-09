"""Does the engine find the right gap and the right lesson? (made-up learners only)

This is the evaluation that matters for the product, and it needs known hidden mastery, so it
can only run on simulated learners. At the end of each module quick check we ask the engine
what it would recommend, then compare with what the learner truly did not know.

Definitions (all from the hidden truth in `simulate.py`):

* True gap:      an assessed concept the learner has not mastered.
* True blocker:  an unmastered concept, at or below a true gap in the concept graph, whose own
                 prerequisites are all mastered. It is the thing that has to be fixed first.
* Hidden-prerequisite case: a true gap that has an unmastered prerequisite, so the real
                 blocker is upstream of the concept that was assessed.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from .curriculum import CONCEPTS, MODULES, ancestors, prereqs
from .engine import WEAK, Engine, Event, LearnerState
from .simulate import SimLearner


def true_blockers(truth: dict[str, bool], gap: str) -> set[str]:
    if truth[gap]:
        return set()
    return {a for a in ancestors(gap) | {gap} if not truth[a] and all(truth[p] for p in prereqs(a))}


def _events(learner: SimLearner, n: int) -> list[Event]:
    return [Event(r.concepts, r.correct, r.unsure) for r in learner.responses[:n]]


def _check_responses(learner: SimLearner, module: str, n: int):
    start = next(i for i, r in enumerate(learner.responses) if r.module == module)
    return learner.responses[start:n]


def recommend_wrong_answer(check) -> str | None:
    """Status quo: study the concept of a question you got wrong (deepest concept wins)."""
    wrong = [r for r in check if not r.correct]
    if not wrong:
        return None
    tags = [c for r in wrong for c in r.concepts]
    return max(tags, key=lambda c: CONCEPTS[c]["col"])


@dataclass
class Tally:
    points: int = 0
    with_gap: int = 0  # points where the learner truly has a gap
    no_gap: int = 0
    recommended: int = 0
    hits: int = 0  # recommended concept is a true blocker of some true gap
    unmastered_hits: int = 0  # recommended concept is truly unmastered
    misses: int = 0  # true gap but nothing recommended
    false_alarms: int = 0  # no true gap but something recommended
    hidden_points: int = 0
    hidden_hits: int = 0
    hidden_exact_gap: int = 0  # hidden case where the recommendation was the assessed gap itself (the shallow answer)
    gap_tp: int = 0
    gap_fp: int = 0
    gap_fn: int = 0

    def summary(self) -> dict[str, float]:
        div = lambda a, b: a / b if b else float("nan")  # noqa: E731
        prec = div(self.gap_tp, self.gap_tp + self.gap_fp)
        rec = div(self.gap_tp, self.gap_tp + self.gap_fn)
        return {
            "points": self.points,
            "with_true_gap": self.with_gap,
            "recommendation_is_true_blocker": div(self.hits, self.with_gap),
            "recommendation_is_unmastered": div(self.unmastered_hits, max(self.recommended - self.false_alarms, 1)),
            "missed_gap_rate": div(self.misses, self.with_gap),
            "false_alarm_rate": div(self.false_alarms, self.no_gap),
            "hidden_prereq_cases": self.hidden_points,
            "hidden_prereq_blocker_hit": div(self.hidden_hits, self.hidden_points),
            "hidden_prereq_stopped_at_assessed_concept": div(self.hidden_exact_gap, self.hidden_points),
            "gap_precision": prec,
            "gap_recall": rec,
            "gap_f1": div(2 * prec * rec, prec + rec) if prec == prec and rec == rec else float("nan"),
        }


def evaluate_diagnosis(learners: list[SimLearner], engine_params) -> dict[str, dict]:
    variants = {
        "Study what you got wrong (status quo)": None,
        "BKT, recommend the assessed concept": Engine(engine_params, use_prerequisites=False),
        "BKT + prerequisite walk": Engine(engine_params, use_prerequisites=True),
    }
    tallies = {name: Tally() for name in variants}
    mastery_probs: list[float] = []
    mastery_truth: list[int] = []

    for lr in learners:
        for ap in lr.assess_points:
            events = _events(lr, ap.n_responses)
            check = _check_responses(lr, ap.module, ap.n_responses)
            truth = ap.truth
            gaps = [c for c in ap.assessed if not truth[c]]
            blockers = set().union(*(true_blockers(truth, g) for g in gaps)) if gaps else set()
            hidden = [g for g in gaps if true_blockers(truth, g) != {g}]

            base_engine = variants["BKT + prerequisite walk"]
            state = base_engine.trace(LearnerState(), events)
            for c in ap.assessed:
                if state.observations.get(c):
                    mastery_probs.append(base_engine.mastery_of(state, c))
                    mastery_truth.append(int(truth[c]))

            for name, eng in variants.items():
                t = tallies[name]
                t.points += 1
                if eng is None:
                    rec_concept = recommend_wrong_answer(check)
                    predicted_gaps = {c for r in check if not r.correct for c in r.concepts if c in ap.assessed}
                    observed_gap = rec_concept
                else:
                    st = eng.trace(LearnerState(), events)
                    rec = eng.recommend(st, ap.assessed)
                    rec_concept = rec["concept_id"] if rec else None
                    observed_gap = rec["observed_concept_id"] if rec else None
                    predicted_gaps = {c for c in ap.assessed if st.observations.get(c) and eng.mastery_of(st, c) < WEAK}

                for c in ap.assessed:
                    pred, true_gap = c in predicted_gaps, not truth[c]
                    t.gap_tp += pred and true_gap
                    t.gap_fp += pred and not true_gap
                    t.gap_fn += (not pred) and true_gap

                if gaps:
                    t.with_gap += 1
                    if rec_concept is None:
                        t.misses += 1
                    else:
                        t.recommended += 1
                        t.hits += rec_concept in blockers
                        t.unmastered_hits += not truth[rec_concept]
                else:
                    t.no_gap += 1
                    if rec_concept is not None:
                        t.recommended += 1
                        t.false_alarms += 1

                if hidden:
                    t.hidden_points += 1
                    t.hidden_hits += rec_concept in blockers if rec_concept else False
                    t.hidden_exact_gap += rec_concept is not None and rec_concept == observed_gap and rec_concept in gaps

    out = {name: t.summary() for name, t in tallies.items()}
    out["_mastery_estimates"] = mastery_quality(np.array(mastery_probs), np.array(mastery_truth))
    return out


def mastery_quality(p: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    """How well P(mastered) matches the hidden mastered flag, over assessed concepts."""
    from sklearn.metrics import roc_auc_score

    return {
        "n": int(len(p)),
        "auc": float(roc_auc_score(truth, p)) if 0 < truth.mean() < 1 else float("nan"),
        "brier": float(np.mean((p - truth) ** 2)),
        "mean_abs_error": float(np.mean(np.abs(p - truth))),
        "share_truly_mastered": float(truth.mean()),
    }
