"""Draw the headline result: baseline against improved model on learners in Barabari's quiz format.

    python scripts/plot_results.py

Reads results/model_comparison.json (nothing is refitted) and writes results/model_comparison.png:
the mean over the 5 evaluation runs, with the run-to-run range as error bars.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE, IMP = "Baseline: BKT + prerequisite walk", "Improved: + more evidence before a lesson"

# (key, label, higher is better)
MEASURES = [
    ("hidden_prereq_blocker_hit", "Hidden root cause\nfound", True),
    ("known_concept_recommended", "Lesson on a concept\nalready known", False),
    ("false_alarm_rate", "False alarms", False),
]


def main() -> None:
    runs = json.loads((ROOT / "results" / "model_comparison.json").read_text(encoding="utf8"))["barabari"]
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=150)
    x = np.arange(len(MEASURES))
    w = 0.36
    for k, (name, label, color) in enumerate(((BASE, "Baseline", "#8a96a3"), (IMP, "Improved model", "#b5562a"))):
        vals = np.array([[r["diagnosis"][name][m] * 100 for m, _, _ in MEASURES] for r in runs])
        mean = vals.mean(axis=0)
        err = np.vstack([mean - vals.min(axis=0), vals.max(axis=0) - mean])
        bars = ax.bar(x + (k - 0.5) * w, mean, w, label=label, color=color, yerr=err, capsize=3, error_kw={"elinewidth": 1, "ecolor": "#444"})
        for b, v, top in zip(bars, mean, err[1]):
            ax.text(b.get_x() + b.get_width() / 2, v + top + 1.5, f"{v:.0f}%", ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([label for _, label, _ in MEASURES])
    for xi, (_, _, higher) in zip(x, MEASURES):
        ax.text(xi, -13, "higher is better" if higher else "lower is better", ha="center", fontsize=8.5, color="#555", style="italic")
    ax.set_ylim(0, 80)
    ax.set_ylabel("% of cases")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title(f"{len(runs)} runs of 3,000 simulated learners in Barabari's quiz format (bars: mean, lines: range)", fontsize=9.5, color="#444")
    fig.tight_layout()
    out = ROOT / "results" / "model_comparison.png"
    fig.savefig(out, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()
