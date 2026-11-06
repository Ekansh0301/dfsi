"""Failure analysis: why does the engine miss the true blocker?

For every "hidden prerequisite" assessment point on made-up learners (the real blocker is an
unmastered prerequisite of the assessed gap), classify what happened.

    python scripts/failure_analysis.py

The first column is the Sprint 2 analysis (Sprint 2 simulator, hand-set parameters), unchanged.
The others use parameters fitted on the training learners, for the baseline and the improved
model, on both simulators (seed 0, 2,100 training and 900 test learners).
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from circuit_coach import bkt, prediction
from circuit_coach.curriculum import CONCEPT_ORDER
from circuit_coach.diagnosis_eval import _events, true_blockers
from circuit_coach.engine import BASELINE, IMPROVED, WEAK, Engine, LearnerState
from circuit_coach.simulate import SimConfig, simulate

ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = [
    "Found the true blocker",
    "Recommended a concept the learner actually knew",
    "Blocker was asked about but looked fine",
    "Recommended a real gap, but the real blocker was further upstream",
    "Blocker was never asked about",
    "Engine saw no gap at all",
]


def classify(engine: Engine, test) -> tuple[Counter, int]:
    outcome: Counter[str] = Counter()
    for lr in test:
        for ap in lr.assess_points:
            gaps = [c for c in ap.assessed if not ap.truth[c]]
            hidden = [g for g in gaps if true_blockers(ap.truth, g) != {g}]
            if not hidden:
                continue
            blockers = set().union(*(true_blockers(ap.truth, g) for g in gaps))
            state = engine.trace(LearnerState(), _events(lr, ap.n_responses))
            rec = engine.recommend(state, ap.assessed)
            if rec is None:
                outcome["Engine saw no gap at all"] += 1
            elif rec["concept_id"] in blockers:
                outcome["Found the true blocker"] += 1
            else:
                missing = [b for b in blockers if not state.observations.get(b)]
                weak_seen = [b for b in blockers if state.observations.get(b) and engine.mastery_of(state, b) < WEAK]
                if missing and len(missing) == len(blockers):
                    outcome["Blocker was never asked about"] += 1
                elif not weak_seen:
                    outcome["Blocker was asked about but looked fine"] += 1
                elif ap.truth[rec["concept_id"]]:
                    outcome["Recommended a concept the learner actually knew"] += 1
                else:
                    outcome["Recommended a real gap, but the real blocker was further upstream"] += 1
    return outcome, sum(outcome.values())


def to_seqs(learners):
    return [[(r.item_id, r.concepts, int(r.correct), r.unsure, r.question_type, r.score, r.attempt) for r in lr.responses] for lr in learners]


def main() -> None:
    columns: dict[str, tuple[Counter, int]] = {}
    for sim in ("sprint2", "barabari"):
        learners, _ = simulate(3000, 0, SimConfig.named(sim))
        train, test = learners[:2100], learners[2100:]
        label = "Sprint 2 sim" if sim == "sprint2" else "Barabari sim"
        if sim == "sprint2":
            columns[f"{label}, hand-set (Sprint 2)"] = classify(Engine({c: bkt.HAND_SET for c in CONCEPT_ORDER}), test)
        tr = to_seqs(train)
        base = prediction.BKTPredictor().fit(tr)
        first = prediction.BKTPredictor(max_tags=1, item_difficulty=True).fit(tr)
        columns[f"{label}, baseline"] = classify(Engine({c: base.params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}, options=BASELINE), test)
        columns[f"{label}, improved"] = classify(
            Engine({c: first.params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}, options=IMPROVED, item_difficulty=first.difficulty), test
        )

    lines = [
        "# Failure analysis: hidden-prerequisite cases",
        "",
        "Made-up learners (seed 0, 900 test learners): what happened at each assessment point where the real blocker is a prerequisite of the gap the quick check showed. "
        "The first column is the Sprint 2 analysis (hand-set parameters); the others use fitted parameters.",
        "",
        "| What happened | " + " | ".join(columns) + " |",
        "|---|" + "---|" * len(columns),
        "| Cases | " + " | ".join(f"{t:,}" for _, t in columns.values()) + " |",
    ]
    for k in OUTCOMES:
        lines.append(f"| {k} | " + " | ".join(f"{c[k] / t * 100:.1f}%" for c, t in columns.values()) + " |")
    lines += [
        "",
        "Reading: with fitted parameters the improved model cuts lessons on a concept the learner already knew (20.2% to 13.0% on the Sprint 2 simulator, 41.8% to 18.4% on the Barabari one), "
        "because a wrong answer on a two-concept question no longer blames both. The cost is more blockers that looked fine (8.5% to 9.8%, and 4.2% to 14.9%): "
        "a prerequisite's second tags no longer count as evidence about it, so it is judged on fewer answers. Asking about each prerequisite directly would close that gap.",
    ]
    (ROOT / "results" / "failure_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
