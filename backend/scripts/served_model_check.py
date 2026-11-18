"""Measure the model exactly as the service serves it.

    python scripts/served_model_check.py [--learners 3000] [--seeds 5]

`compare_models.py` evaluates the improved model with per-question difficulty estimated from the
simulator's own answers. The service applies difficulty from `circuit_coach/item_difficulty.json`,
which stays empty until the service has answers for its questions (see
`scripts/estimate_item_difficulty.py`). This script runs the same learners and seeds three ways:

    baseline            standard BKT plus the prerequisite walk
    improved + table    the improved model with difficulty from the simulator's answers
    improved as served  the improved model with no difficulty table (every question average)

and writes the paired differences with 95% intervals (same method as `paired_comparison.py`) to
`results/served_model.md` and `.json`. It changes no shipped file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import paired_comparison as pc
from compare_models import to_seqs
from circuit_coach import bkt, prediction
from circuit_coach.curriculum import CONCEPT_ORDER
from circuit_coach.diagnosis_eval import evaluate_diagnosis
from circuit_coach.engine import BASELINE, IMPROVED, Engine
from circuit_coach.simulate import SimConfig, simulate

ROOT = Path(__file__).resolve().parents[1]
DIAG = [m for m in pc.MEASURES if m[0] == "diagnosis"]


def run_seed(sim: str, seed: int, n: int) -> dict:
    learners, _ = simulate(n, seed, SimConfig.named(sim))
    cut = int(0.7 * n)
    tr, test = to_seqs(learners[:cut]), learners[cut:]
    first = prediction.BKTPredictor(max_tags=1).fit(tr)
    with_difficulty = prediction.BKTPredictor(max_tags=1, item_difficulty=True).fit(tr)
    allt = prediction.BKTPredictor().fit(tr)
    p_all = {c: allt.params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}
    p_first = {c: first.params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}
    engines = {
        "baseline": Engine(p_all, options=BASELINE),
        "table": Engine(p_first, options=IMPROVED, item_difficulty=with_difficulty.difficulty),
        "served": Engine(p_first, options=IMPROVED, item_difficulty={}),
    }
    out = {}
    for name, eng in engines.items():
        d = evaluate_diagnosis(test, None, {name: eng})[name]
        d["known_concept_recommended"] = 1 - d["recommendation_is_unmastered"]
        out[name] = d
    return out


def compare(runs: list[dict], base: str, other: str) -> list[dict]:
    pc.MEASURES = DIAG
    shaped = [{"diagnosis": {pc.BASE_DIAG: r[base], pc.IMP_DIAG: r[other]}} for r in runs]
    return pc.paired(shaped)


def table(rows: list[dict]) -> list[str]:
    lines = ["| Measure | Mean difference | Median difference | 95% interval | Better in | Verdict |", "|---|---|---|---|---|---|"]
    for r in rows:
        lo, hi = r["ci95"]
        lines.append(
            f"| {r['measure']} ({'higher' if r['higher_is_better'] else 'lower'} is better) | {pc.fmt(r['mean_diff'], True)} | {pc.fmt(r['median_diff'], True)} | "
            f"{pc.fmt(lo, True)} to {pc.fmt(hi, True)} | {r['better_runs']} of {r['runs']} runs | {r['verdict']} |"
        )
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--learners", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()
    results: dict = {}
    lines = [
        "# The improved model as the service serves it",
        "",
        "Same learners and seeds as `model_comparison.md` (5 runs of 3,000 made-up learners per simulator). The service ships an empty per-question difficulty table until it has "
        "answers for its own questions, so every question counts as average. Differences are within each run, with 95% intervals over the runs (`paired_comparison.py`).",
    ]
    summary = {"better": 0, "worse": 0, "no clear difference": 0}
    for sim, label in (("sprint2", "Sprint 2 simulator"), ("barabari", "Barabari's quiz format")):
        runs = [run_seed(sim, s, args.learners) for s in range(args.seeds)]
        vs_base, vs_table = compare(runs, "baseline", "served"), compare(runs, "table", "served")
        results[sim] = {"served_vs_baseline": vs_base, "served_vs_table": vs_table}
        lines += ["", f"## {label}", "", "### As served against the baseline", ""] + table(vs_base)
        lines += ["", "### As served against the improved model with a difficulty table", ""] + table(vs_table)
        for r in vs_base:
            summary[r["verdict"]] += 1
    total = sum(summary.values())
    lines += [
        "",
        "## Summary",
        "",
        f"Against the baseline, the improved model as served is clearly better on {summary['better']} of {total} diagnosis measures, clearly worse on {summary['worse']}, "
        f"and not clearly different on {summary['no clear difference']}.",
    ]
    (ROOT / "results" / "served_model.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf8")
    (ROOT / "results" / "served_model.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
