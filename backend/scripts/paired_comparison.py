"""Paired comparison of the improved model against the baseline, run by run.

    python scripts/paired_comparison.py

Reads results/model_comparison.json (written by compare_models.py; nothing is refitted) and,
for each measure, takes the difference improved minus baseline within each evaluation seed. Both
models see the same learners in a seed, so the paired difference removes the run-to-run spread
that the mean ± standard deviation tables mix in. Reports the mean difference, a 95% interval
(t distribution over the seeds), and in how many seeds the improved model was better.

Writes results/paired_comparison.md and .json.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BASE_DIAG, IMP_DIAG = "Baseline: BKT + prerequisite walk", "Improved: + more evidence before a lesson"
BASE_PRED, IMP_PRED = "Baseline: BKT, fitted", "Improved: + prerequisite-aware learning"

# (section, key, label, higher is better, shown as a percentage)
MEASURES = [
    ("diagnosis", "gap_f1", "Gap F1", True, True),
    ("diagnosis", "recommendation_is_true_blocker", "True blocker", True, True),
    ("diagnosis", "hidden_prereq_blocker_hit", "Hidden blocker found", True, True),
    ("diagnosis", "known_concept_recommended", "Recommended a known concept", False, True),
    ("diagnosis", "missed_gap_rate", "Missed gaps", False, True),
    ("diagnosis", "false_alarm_rate", "False alarms", False, True),
    ("prediction", "auc", "Next-answer AUC", True, False),
]

# Two-sided 95% critical values of Student's t by degrees of freedom.
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
       15: 2.131, 20: 2.086, 30: 2.042}


def t95(df: int) -> float:
    if df in T95:
        return T95[df]
    smaller = [k for k in T95 if k <= df]
    return T95[max(smaller)] if smaller else T95[1]


def paired(runs: list[dict]) -> list[dict]:
    rows = []
    for section, key, label, higher, pct in MEASURES:
        base, imp = (BASE_DIAG, IMP_DIAG) if section == "diagnosis" else (BASE_PRED, IMP_PRED)
        b = [r[section][base][key] for r in runs]
        i = [r[section][imp][key] for r in runs]
        diffs = [y - x for x, y in zip(b, i)]
        n = len(diffs)
        mean = statistics.fmean(diffs)
        half = t95(n - 1) * statistics.stdev(diffs) / math.sqrt(n) if n > 1 else float("inf")
        lo, hi = mean - half, mean + half
        better_runs = sum((d > 0) if higher else (d < 0) for d in diffs)
        if (lo > 0 and higher) or (hi < 0 and not higher):
            verdict = "better"
        elif (hi < 0 and higher) or (lo > 0 and not higher):
            verdict = "worse"
        else:
            verdict = "no clear difference"
        rows.append({
            "measure": label, "higher_is_better": higher, "percent": pct, "baseline": b, "improved": i,
            "mean_diff": mean, "median_diff": statistics.median(diffs), "ci95": [lo, hi], "better_runs": better_runs, "runs": n, "verdict": verdict,
        })
    return rows


def fmt(x: float, pct: bool) -> str:
    return f"{x * 100:+.1f} pts" if pct else f"{x:+.3f}"


def render(results: dict[str, list[dict]]) -> list[str]:
    lines = [
        "# Improved model against the baseline, paired by run",
        "",
        "Each evaluation seed gives both models the same made-up learners, so the difference is taken within a seed (improved minus baseline) and then averaged. "
        "The 95% interval uses the t distribution over the seeds. \"Better\" or \"worse\" means the interval excludes zero; otherwise the difference is within the noise of 5 runs. "
        "Source: `results/model_comparison.json`.",
    ]
    summary = {"better": 0, "worse": 0, "no clear difference": 0}
    for sim, label in (("sprint2", "Sprint 2 simulator"), ("barabari", "Barabari's quiz format")):
        lines += ["", f"## {label}", "", "| Measure | Mean difference | Median difference | 95% interval | Improved better in | Verdict |", "|---|---|---|---|---|---|"]
        for r in results[sim]:
            pct = r["percent"]
            lo, hi = r["ci95"]
            lines.append(
                f"| {r['measure']} ({'higher' if r['higher_is_better'] else 'lower'} is better) | {fmt(r['mean_diff'], pct)} | {fmt(r['median_diff'], pct)} | "
                f"{fmt(lo, pct)} to {fmt(hi, pct)} | {r['better_runs']} of {r['runs']} runs | {r['verdict']} |"
            )
            summary[r["verdict"]] += 1
    total = sum(summary.values())
    lines += [
        "",
        "## Summary",
        "",
        f"Of {total} measures, the improved model is clearly better on {summary['better']}, clearly worse on {summary['worse']}, "
        f"and not clearly different on {summary['no clear difference']}.",
        "",
        "Read the run counts with the interval: a measure can be within the noise overall and still be worse in most runs, as missed gaps on the Sprint 2 simulator are "
        "(one baseline run at 6.4% widens the interval; the median difference is the better guide there).",
    ]
    return lines


def main() -> None:
    runs = json.loads((ROOT / "results" / "model_comparison.json").read_text(encoding="utf8"))
    results = {sim: paired(runs[sim]) for sim in ("sprint2", "barabari")}
    (ROOT / "results" / "paired_comparison.json").write_text(json.dumps(results, indent=1) + "\n", encoding="utf8")
    lines = render(results)
    (ROOT / "results" / "paired_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
