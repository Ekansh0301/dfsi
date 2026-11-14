"""Does knowledge tracing earn its place? BKT against plain accuracy with the same walk.

    python scripts/accuracy_baseline.py [--learners 3000] [--seeds 5]

BKT without the prerequisite walk finds fewer true blockers than "study what you got wrong", so
the gain comes from the walk. This script gives the walk to a much simpler mastery estimate, the
learner's smoothed accuracy so far (circuit_coach/accuracy_engine.py), and scores it on the same
made-up learners, seeds and split as results/model_comparison.json. The BKT rows are read from
that file (nothing is refitted); the status quo and accuracy rows are computed here.

Writes results/accuracy_baseline.md and .json.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path

from circuit_coach.accuracy_engine import AccuracyEngine
from circuit_coach.diagnosis_eval import evaluate_diagnosis
from circuit_coach.engine import ModelOptions
from circuit_coach.simulate import SimConfig, simulate

ROOT = Path(__file__).resolve().parents[1]

STATUS_QUO = "Study what you got wrong (status quo)"
ACC = "Accuracy + prerequisite walk"
ACC2 = "Accuracy + prerequisite walk, 2 answers before a lesson"
BKT_BASE = "Baseline: BKT + prerequisite walk"
BKT_IMP = "Improved: + more evidence before a lesson"
ROWS = [STATUS_QUO, ACC, ACC2, BKT_BASE, BKT_IMP]
LABELS = {BKT_BASE: "BKT baseline + prerequisite walk", BKT_IMP: "BKT improved model (2 answers before a lesson)"}

KEYS = [
    ("gap_f1", "Gap F1", True),
    ("recommendation_is_true_blocker", "True blocker", True),
    ("hidden_prereq_blocker_hit", "Hidden blocker found", True),
    ("known_concept_recommended", "Recommended a known concept", False),
    ("missed_gap_rate", "Missed gaps", False),
    ("false_alarm_rate", "False alarms", False),
]
T95_4 = 2.776  # two-sided 95% t value for 5 runs


def run_seed(sim: str, seed: int, n: int) -> dict:
    learners, _ = simulate(n, seed, SimConfig.named(sim))
    test = learners[int(0.7 * n):]
    variants = {
        STATUS_QUO: None,
        ACC: AccuracyEngine(),
        ACC2: AccuracyEngine(ModelOptions("acc2", min_evidence=2, strong_evidence=0.4)),
    }
    out = {}
    for name, eng in variants.items():
        d = evaluate_diagnosis(test, None, {name: eng} if eng is not None else {name: None, "_ref": AccuracyEngine()})[name]
        d["known_concept_recommended"] = 1 - d["recommendation_is_unmastered"]
        out[name] = d
    return out


def ci(diffs: list[float]) -> tuple[float, float, float]:
    m = statistics.fmean(diffs)
    h = T95_4 * statistics.stdev(diffs) / math.sqrt(len(diffs)) if len(diffs) > 1 else float("inf")
    return m, m - h, m + h


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--learners", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    comparison = json.loads((ROOT / "results" / "model_comparison.json").read_text(encoding="utf8"))
    if args.learners != 3000 or args.seeds > len(comparison["sprint2"]):
        raise SystemExit("The BKT rows come from results/model_comparison.json (3000 learners, 5 seeds); run with the defaults.")
    t0 = time.time()
    results: dict[str, list[dict]] = {}
    for sim in ("sprint2", "barabari"):
        results[sim] = []
        for seed in range(args.seeds):
            row = run_seed(sim, seed, args.learners)
            ref = comparison[sim][seed]
            assert ref["seed"] == seed and ref["sim"] == sim
            row[BKT_BASE] = ref["diagnosis"][BKT_BASE]
            row[BKT_IMP] = ref["diagnosis"][BKT_IMP]
            results[sim].append(row)
            print(f"{sim} seed {seed} done ({time.time() - t0:.0f}s)", flush=True)
    (ROOT / "results" / "accuracy_baseline.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf8")

    lines = [
        "# Knowledge tracing against plain accuracy, with the same prerequisite walk",
        "",
        f"{args.seeds} runs of {args.learners} made-up learners per simulator, the same seeds and 70:30 split as `results/model_comparison.md` (scored on the 30% test learners). "
        "The accuracy engine estimates mastery as (right + 1) / (answers + 2) and otherwise uses the same 0.6 threshold, prerequisite walk and lesson choice "
        "(`circuit_coach/accuracy_engine.py`). BKT rows are copied from `results/model_comparison.json`. Mean over runs.",
    ]
    for sim, label in (("sprint2", "Sprint 2 simulator"), ("barabari", "Barabari's quiz format")):
        runs = results[sim]
        lines += ["", f"## {label}", "", "| Method | " + " | ".join(h for _, h, _ in KEYS) + " |", "|---|" + "---|" * len(KEYS)]
        for name in ROWS:
            vals = [statistics.fmean(r[name][k] for r in runs) for k, _, _ in KEYS]
            lines.append(f"| {LABELS.get(name, name)} | " + " | ".join(f"{v * 100:.1f}%" for v in vals) + " |")
        lines += ["", "Paired difference, BKT minus accuracy with the same evidence rule (mean and 95% interval over runs; positive is better for BKT on every row):", "",
                  "| Measure | BKT baseline vs accuracy | BKT improved vs accuracy (2 answers) |", "|---|---|---|"]
        for k, h, higher in KEYS:
            sign = 1 if higher else -1
            cells = []
            for bkt_name, acc_name in ((BKT_BASE, ACC), (BKT_IMP, ACC2)):
                m, lo, hi = ci([sign * (r[bkt_name][k] - r[acc_name][k]) for r in runs])
                cells.append(f"{m * 100:+.1f} pts ({lo * 100:+.1f} to {hi * 100:+.1f})")
            lines.append(f"| {h} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Reading",
        "",
        "- With the same walk, BKT finds clearly more true blockers and hidden blockers than accuracy, and recommends far fewer concepts the learner already knew, "
        "on both simulators. Accuracy never forgets an early wrong answer, so it keeps sending learners back to concepts they have since learned.",
        "- Accuracy misses slightly fewer gaps (it calls a gap after a single wrong answer), at the cost of more lessons on the wrong concept.",
        "- So the gain over \"study what you got wrong\" comes from the walk and from BKT together: the walk on plain accuracy recovers part of it, BKT the rest.",
    ]
    (ROOT / "results" / "accuracy_baseline.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines))
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
