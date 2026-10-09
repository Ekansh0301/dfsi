"""Failure analysis: do questions tagged with several concepts bias the fitted BKT parameters?

Fits each concept twice on the same made-up learners: once using every answer tagged with the
concept (what the baseline does), once using only single-concept questions. The true slip
rate in the simulator is 0.04 to 0.14 (mean 0.09).

    python scripts/ablation_multitag.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from circuit_coach import bkt
from circuit_coach.curriculum import CONCEPT_ORDER
from circuit_coach.simulate import simulate

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    learners, _ = simulate(3000, 0)
    train = learners[:2100]
    lines = [
        "# Failure analysis: multi-concept questions bias the fitted parameters",
        "",
        "Made-up learners (seed 0, 2,100 training learners). The simulator's true slip is 0.04 to 0.14 (mean 0.09). The fitting limit for slip is 0.30.",
        "",
        "| Concept | Slip, all tagged answers | Slip, single-concept questions only |",
        "|---|---|---|",
    ]
    rows = []
    for c in CONCEPT_ORDER:
        every = [np.array([int(r.correct) for r in lr.responses if c in r.concepts]) for lr in train]
        single = [np.array([int(r.correct) for r in lr.responses if r.concepts == (c,)]) for lr in train]
        pa = bkt.fit_params([s for s in every if len(s) >= 2])
        ps = bkt.fit_params([s for s in single if len(s) >= 2])
        rows.append((pa.p_slip, ps.p_slip))
        lines.append(f"| {c} | {pa.p_slip:.2f} | {ps.p_slip:.2f} |")
    r = np.array(rows)
    lines += [
        "",
        f"Mean slip: {r[:, 0].mean():.2f} using all tagged answers, {r[:, 1].mean():.2f} using single-concept questions only. Concepts at the 0.30 limit: {(r[:, 0] >= 0.29).sum()} of 10 against {(r[:, 1] >= 0.29).sum()} of 10.",
        "",
        "Reading: when a question needs several concepts and is answered wrongly, plain BKT blames every tagged concept. That makes the model think learners often get a mastered concept wrong, so slip is overestimated.",
    ]
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "ablation_multitag.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
