"""Baseline evaluation on made-up learners with known hidden mastery.

    python scripts/run_synthetic.py [--learners 3000] [--seeds 5]

Writes results/synthetic_results.json and results/synthetic_results.md, and saves the
fitted BKT parameters to circuit_coach/fitted_params.json (fitted on the first seed's
training split) so the API uses them.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from circuit_coach import bkt, prediction
from circuit_coach.curriculum import CONCEPT_ORDER
from circuit_coach.diagnosis_eval import evaluate_diagnosis
from circuit_coach.simulate import concept_sequences, simulate

ROOT = Path(__file__).resolve().parents[1]


def to_seqs(learners):
    return [[(r.item_id, r.concepts, int(r.correct), r.unsure) for r in lr.responses] for lr in learners]


def run_seed(seed: int, n_learners: int) -> dict:
    learners, _ = simulate(n_learners, seed)
    cut = int(0.7 * len(learners))
    train, test = learners[:cut], learners[cut:]
    train_seqs, test_seqs = to_seqs(train), to_seqs(test)

    ladder = {}
    fitted = None
    for make in prediction.standard_ladder():
        p = make().fit(train_seqs)
        ladder[p.name] = prediction.evaluate(p, test_seqs, skip_first=3)
        if isinstance(p, prediction.BKTPredictor) and p.fit_params:
            fitted = p.params

    fitted_params = {c: fitted.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}
    hand = {c: bkt.HAND_SET for c in CONCEPT_ORDER}
    diagnosis = {
        "fitted": evaluate_diagnosis(test, fitted_params),
        "hand_set": evaluate_diagnosis(test, hand),
    }
    return {"seed": seed, "ladder": ladder, "diagnosis": diagnosis, "fitted_params": {c: p.as_dict() for c, p in fitted_params.items()}}


def mean_std(runs: list[dict], path: list[str]) -> tuple[float, float]:
    vals = []
    for r in runs:
        v = r
        for k in path:
            v = v[k]
        vals.append(v)
    a = np.array(vals, dtype=float)
    return float(np.nanmean(a)), float(np.nanstd(a))


def fmt(m: float, s: float, pct: bool = False) -> str:
    return f"{m * 100:.1f}% ± {s * 100:.1f}" if pct else f"{m:.3f} ± {s:.3f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--learners", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    t0 = time.time()
    runs = []
    for seed in range(args.seeds):
        runs.append(run_seed(seed, args.learners))
        print(f"seed {seed} done ({time.time() - t0:.0f}s)", flush=True)

    # fitted parameters from the first seed go to the service
    params_file = ROOT / "circuit_coach" / "fitted_params.json"
    params_file.write_text(
        json.dumps(
            {
                "source": f"EM fit on {int(0.7 * args.learners)} made-up learners (seed 0). Placeholder until real learner data exists.",
                "concepts": runs[0]["fitted_params"],
            },
            indent=2,
        )
        + "\n"
    )

    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "synthetic_results.json").write_text(json.dumps(runs, indent=1) + "\n")

    lines = [f"# Baseline results on made-up learners", "", f"{args.seeds} runs, {args.learners} learners each (70% train, 30% test). Mean ± standard deviation across runs.", ""]
    lines += ["## 1. Predicting the next answer", "", "| Method | AUC | Accuracy | Log loss | RMSE |", "|---|---|---|---|---|"]
    for name in runs[0]["ladder"]:
        row = [fmt(*mean_std(runs, ["ladder", name, k])) for k in ("auc", "accuracy", "log_loss", "rmse")]
        lines.append(f"| {name} | " + " | ".join(row) + " |")

    for tag, label in (("fitted", "fitted parameters"), ("hand_set", "hand-set parameters")):
        lines += ["", f"## 2{'a' if tag == 'fitted' else 'b'}. Finding the gap and the lesson ({label})", ""]
        lines += ["| Method | Gap F1 | Recommendation is a true blocker | Hidden-prerequisite cases: blocker found | ...stopped at the assessed concept | Missed gaps | False alarms |", "|---|---|---|---|---|---|---|"]
        for name in runs[0]["diagnosis"][tag]:
            if name.startswith("_"):
                continue
            g = lambda k: fmt(*mean_std(runs, ["diagnosis", tag, name, k]), pct=True)  # noqa: E731
            lines.append(f"| {name} | {g('gap_f1')} | {g('recommendation_is_true_blocker')} | {g('hidden_prereq_blocker_hit')} | {g('hidden_prereq_stopped_at_assessed_concept')} | {g('missed_gap_rate')} | {g('false_alarm_rate')} |")
        m = lambda k: fmt(*mean_std(runs, ["diagnosis", tag, "_mastery_estimates", k]))  # noqa: E731
        lines += ["", f"Mastery estimates vs hidden truth ({label}): AUC {m('auc')}, Brier score {m('brier')}, mean absolute error {m('mean_abs_error')}."]

    lines += ["", "## 3. Fitted parameters (seed 0)", "", "| Concept | p_init | p_learn | p_slip | p_guess |", "|---|---|---|---|---|"]
    for c, d in runs[0]["fitted_params"].items():
        lines.append(f"| {c} | {d['p_init']:.2f} | {d['p_learn']:.2f} | {d['p_slip']:.2f} | {d['p_guess']:.2f} |")
    (ROOT / "results" / "synthetic_results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
