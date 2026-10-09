"""Failure analysis: why does the prerequisite walk miss the true blocker?

For every "hidden prerequisite" assessment point on made-up learners (the real blocker is an
unmastered prerequisite of the assessed gap), classify what happened to the baseline engine.

    python scripts/failure_analysis.py
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from circuit_coach import bkt
from circuit_coach.curriculum import CONCEPT_ORDER
from circuit_coach.diagnosis_eval import _events, true_blockers
from circuit_coach.engine import WEAK, Engine, LearnerState
from circuit_coach.simulate import simulate

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    learners, _ = simulate(3000, 0)
    test = learners[2100:]
    engine = Engine({c: bkt.HAND_SET for c in CONCEPT_ORDER})
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
    total = sum(outcome.values())
    lines = [
        "# Failure analysis: hidden-prerequisite cases",
        "",
        f"Made-up learners (seed 0, 900 test learners), hand-set parameters, {total} assessment points where the real blocker is a prerequisite.",
        "",
        "| What happened | Share |",
        "|---|---|",
    ]
    for k, v in outcome.most_common():
        lines.append(f"| {k} | {v / total * 100:.1f}% |")
    (ROOT / "results" / "failure_analysis.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
