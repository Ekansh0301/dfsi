"""Calibration of the engine's numbers (PLAN S4-3).

    python scripts/calibration.py [--learners 3000] [--seeds 3]

Two questions, on made-up learners with Barabari's quiz format (test learners only):

1. Next answer: when the model says "70% chance of a right answer", are about 70% right?
2. Mastery: when the engine says P(mastered) = 0.7 at the end of a quick check, are about 70%
   of those learners truly mastered (hidden truth)? The 0.6 gap threshold relies on this.

Predictions are grouped in 10 bins of equal width. The expected calibration error (ECE) is the
answer-weighted mean gap between predicted and observed. Writes results/calibration.md, .json
and results/calibration.png.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from circuit_coach import bkt, prediction
from circuit_coach.curriculum import CONCEPT_ORDER, CONCEPTS
from circuit_coach.diagnosis_eval import _events
from circuit_coach.engine import BASELINE, IMPROVED, Engine, LearnerState
from circuit_coach.simulate import SimConfig, simulate

ROOT = Path(__file__).resolve().parents[1]
PREREQS = {c: d["prereqs"] for c, d in CONCEPTS.items()}
EDGES = np.linspace(0, 1, 11)


def to_seqs(learners):
    return [[(r.item_id, r.concepts, int(r.correct), r.unsure, r.question_type, r.score, r.attempt) for r in lr.responses] for lr in learners]


def bins(p: np.ndarray, y: np.ndarray) -> dict:
    idx = np.clip(np.digitize(p, EDGES[1:-1]), 0, 9)
    rows, ece = [], 0.0
    for b in range(10):
        m = idx == b
        if not m.any():
            continue
        pred, obs = float(p[m].mean()), float(y[m].mean())
        rows.append({"bin": f"{EDGES[b]:.1f} to {EDGES[b + 1]:.1f}", "n": int(m.sum()), "predicted": pred, "observed": obs})
        ece += m.sum() / len(p) * abs(pred - obs)
    return {"ece": float(ece), "bins": rows}


def run_seed(seed: int, n: int) -> dict:
    learners, _ = simulate(n, seed, SimConfig())
    cut = int(0.7 * n)
    train, test = learners[:cut], learners[cut:]
    tr, te = to_seqs(train), to_seqs(test)
    models = {
        "baseline": prediction.BKTPredictor().fit(tr),
        "improved": prediction.BKTPredictor(max_tags=1, item_difficulty=True, prereqs=PREREQS, prereq_learn_factor=IMPROVED.prereq_learn_factor).fit(tr),
    }
    out = {"answers": {}, "mastery": {}}
    for name, m in models.items():
        ps, ys = [], []
        for seq in te:
            if len(seq) > 3:
                ps.append(m.predict(seq)[3:])
                ys.append(np.array([s[2] for s in seq])[3:])
        out["answers"][name] = (np.concatenate(ps).tolist(), np.concatenate(ys).tolist())

    engines = {
        "baseline": Engine({c: models["baseline"].params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}, options=BASELINE),
        "improved": Engine(
            {c: models["improved"].params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}, options=IMPROVED, item_difficulty=models["improved"].difficulty
        ),
    }
    for name, eng in engines.items():
        ps, ys = [], []
        for lr in test:
            for ap in lr.assess_points:
                st = eng.trace(LearnerState(), _events(lr, ap.n_responses))
                for c in ap.assessed:
                    if st.observations.get(c):
                        ps.append(eng.mastery_of(st, c))
                        ys.append(int(ap.truth[c]))
        out["mastery"][name] = (ps, ys)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--learners", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()
    t0 = time.time()
    pooled = {"answers": {"baseline": ([], []), "improved": ([], [])}, "mastery": {"baseline": ([], []), "improved": ([], [])}}
    per_seed = []
    for seed in range(args.seeds):
        r = run_seed(seed, args.learners)
        per_seed.append({kind: {m: bins(np.array(p), np.array(y))["ece"] for m, (p, y) in r[kind].items()} for kind in r})
        for kind in r:
            for m, (p, y) in r[kind].items():
                pooled[kind][m][0].extend(p)
                pooled[kind][m][1].extend(y)
        print(f"seed {seed} done ({time.time() - t0:.0f}s)", flush=True)

    result = {kind: {m: bins(np.array(p), np.array(y)) for m, (p, y) in pooled[kind].items()} for kind in pooled}
    result["ece_per_seed"] = per_seed
    (ROOT / "results" / "calibration.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf8")

    titles = {"answers": "Next answer: predicted chance of a right answer", "mastery": "Mastery: estimated P(mastered) against the hidden truth"}
    lines = [
        "# Calibration of the engine's numbers",
        "",
        f"Made-up learners with Barabari's quiz format, test learners of {args.seeds} runs of {args.learners}, pooled. 10 bins of equal width; ECE is the answer-weighted mean gap between predicted and observed (0 is perfect).",
        "",
        "| Quantity | Baseline ECE | Improved ECE |",
        "|---|---|---|",
    ]
    for kind in ("answers", "mastery"):
        e = [np.array([s[kind][m] for s in per_seed]) for m in ("baseline", "improved")]
        lines.append(f"| {titles[kind].split(':')[0]} | {e[0].mean():.3f} ± {e[0].std():.3f} | {e[1].mean():.3f} ± {e[1].std():.3f} |")
    for kind in ("answers", "mastery"):
        n = "Answers" if kind == "answers" else "Estimates"
        lines += ["", f"## {titles[kind]}", "", f"| Bin | {n} (baseline) | Predicted | Observed | {n} (improved) | Predicted | Observed |", "|---|---|---|---|---|---|---|"]
        b, i = ({r["bin"]: r for r in result[kind][m]["bins"]} for m in ("baseline", "improved"))
        for key in [f"{EDGES[k]:.1f} to {EDGES[k + 1]:.1f}" for k in range(10)]:
            rb, ri = b.get(key), i.get(key)
            f = lambda r: (f"{r['n']:,} | {r['predicted']:.2f} | {r['observed']:.2f}" if r else "0 | | ")  # noqa: E731
            lines.append(f"| {key} | {f(rb)} | {f(ri)} |")
    lines += ["", "Plot: `results/calibration.png` (points on the diagonal are perfectly calibrated)."]
    (ROOT / "results" / "calibration.md").write_text("\n".join(lines) + "\n", encoding="utf8")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
        for ax, kind in zip(axes, ("answers", "mastery")):
            ax.plot([0, 1], [0, 1], color="#9a9a9a", lw=1, ls="--", label="Perfect calibration")
            for m, color in (("baseline", "#8c6d1f"), ("improved", "#1f6f8b")):
                rows = result[kind][m]["bins"]
                ax.plot([r["predicted"] for r in rows], [r["observed"] for r in rows], "o-", color=color, label=f"{m} (ECE {result[kind][m]['ece']:.3f})")
            ax.set_title(titles[kind], fontsize=10)
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Observed share")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.legend(fontsize=8, loc="upper left")
        fig.tight_layout()
        fig.savefig(ROOT / "results" / "calibration.png", dpi=120)
    except ImportError:
        print("matplotlib not installed: skipped the plot")
    print("\n".join(lines[:8]))
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
