"""Draw the figures that show how the project was evaluated.

    python scripts/plot_results.py [--out results]

Reads the saved results in results/ (nothing is refitted) and writes PNG figures:

    model_comparison.png     baseline against the improved model on six measures, both simulators
    paired_differences.png   the same, run by run, with 95% intervals (what is clearly better)
    improvement_ladder.png   what each model change adds, one change at a time
    bkt_vs_accuracy.png      does knowledge tracing earn its place against plain accuracy?
    ednet_prediction.png     real student answers (EdNet): next-answer AUC
    robustness.png           wrong tags and a wrong concept graph
    failure_analysis.png     what happens in the hardest cases (a hidden prerequisite)
    test_coverage.png        what the automated tests cover (needs pytest, and node for the app tests)

The calibration figure (calibration.png) is drawn by scripts/calibration.py.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import tempfile
import sys
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.ticker  # noqa: F401

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"

GREY, GREY_L = "#8a96a3", "#c9d0d7"
COPPER, BLUE, GREEN, RED = "#b5562a", "#2c5d8f", "#2f7d4f", "#b3261e"
INK, MUTED = "#222222", "#5b6672"
SIMS = (("sprint2", "Older simulator"), ("barabari", "Barabari's quiz format"))

BASE, IMP = "Baseline: BKT + prerequisite walk", "Improved: + more evidence before a lesson"
STEPS = [
    (BASE, "Baseline"),
    ("+ first-tag credit", "+ first-tag\ncredit"),
    ("+ question difficulty", "+ question\ndifficulty"),
    ("+ prerequisite-aware learning", "+ prerequisite-\naware learning"),
    (IMP, "+ evidence\nrule (improved)"),
]

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white",
})


def load(name: str):
    return json.loads((RES / name).read_text(encoding="utf8"))


def mean_over_runs(runs: list[dict], section: str, name: str, key: str) -> float:
    return statistics.fmean(r[section][name][key] for r in runs) * 100


def save(fig, out: Path, name: str) -> None:
    fig.savefig(out / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", out / name)


def top_pad(key: str, v: float) -> float:
    """Gap above a bar (and its range line) for the value label."""
    return 0.5 if key == "missed_gap_rate" else 1.2


# ------------------------------------------------------------------------------------------
# 1. Headline: baseline against improved, six measures, both simulators
# ------------------------------------------------------------------------------------------
MEASURES6 = [
    ("hidden_prereq_blocker_hit", "Hidden root cause found", True),
    ("recommendation_is_true_blocker", "Lesson is a real blocker", True),
    ("known_concept_recommended", "Lesson on a concept\nthe learner knew", False),
    ("false_alarm_rate", "False alarms", False),
    ("missed_gap_rate", "Missed gaps", False),
    ("gap_f1", "Gap detection (F1)", True),
]


def fig_model_comparison(out: Path) -> None:
    runs = load("model_comparison.json")
    paired = {sim: {r["measure"]: r for r in rows} for sim, rows in load("paired_comparison.json").items()}
    names = {"hidden_prereq_blocker_hit": "Hidden blocker found", "recommendation_is_true_blocker": "True blocker",
             "known_concept_recommended": "Recommended a known concept", "false_alarm_rate": "False alarms",
             "missed_gap_rate": "Missed gaps", "gap_f1": "Gap F1"}
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 7.2))
    fig.suptitle("The improved model finds the real cause more often and wastes fewer lessons", fontsize=14, fontweight="bold", x=0.5, y=0.99)
    fig.text(0.5, 0.945, "5 runs of 3,000 simulated learners per simulator (bars: mean, lines: range). Under each pair: improved minus baseline, run by run.",
             ha="center", fontsize=9.5, color=MUTED)
    for ax, (key, label, higher) in zip(axes.flat, MEASURES6):
        x = np.arange(len(SIMS))
        w = 0.36
        top = 0.0
        for k, (name, lab, color) in enumerate(((BASE, "Baseline", GREY), (IMP, "Improved model", COPPER))):
            vals, lo, hi = [], [], []
            for sim, _ in SIMS:
                v = np.array([r["diagnosis"][name][key] * 100 for r in runs[sim]])
                vals.append(v.mean()); lo.append(v.mean() - v.min()); hi.append(v.max() - v.mean())
            bars = ax.bar(x + (k - 0.5) * w, vals, w, color=color, label=lab, yerr=[lo, hi], capsize=3, error_kw={"elinewidth": 1, "ecolor": "#444"})
            for b, v, h in zip(bars, vals, hi):
                ax.text(b.get_x() + b.get_width() / 2, v + h + top_pad(key, v), f"{v:.1f}%" if key == "missed_gap_rate" else f"{v:.0f}%",
                        ha="center", fontsize=9, fontweight="bold")
            top = max(top, max(v + h for v, h in zip(vals, hi)))
        ax.set_ylim(0, 105 if key == "gap_f1" else top * 1.25)
        ax.set_xticks(x)
        ax.set_xticklabels([s for _, s in SIMS], fontsize=9)
        ax.set_title(label, fontsize=11, fontweight="bold", color=INK, pad=8)
        for xi, (sim, _) in zip(x, SIMS):
            row = paired[sim][names[key]]
            d = row["mean_diff"] * 100
            better = {"better": GREEN, "worse": RED}.get(row["verdict"], MUTED)
            txt = f"{d:+.1f} pts" + ("" if row["verdict"] != "no clear difference" else "\nwithin noise")
            ax.annotate(txt, (xi, 0), xytext=(0, -33), textcoords="offset points", ha="center", va="top", fontsize=8.5, color=better, fontweight="bold")
        ax.annotate("higher is better" if higher else "lower is better", (0.5, 0), xycoords="axes fraction", xytext=(0, -62),
                    textcoords="offset points", ha="center", fontsize=8.5, color=MUTED, style="italic")
        ax.set_ylabel("% of cases" if key != "gap_f1" else "F1 score, %", fontsize=9)
    handles = [plt.Rectangle((0, 0), 1, 1, color=GREY), plt.Rectangle((0, 0), 1, 1, color=COPPER)]
    fig.legend(handles, ["Baseline", "Improved model"], loc="upper center", bbox_to_anchor=(0.5, 0.925), ncol=2, frameon=False, fontsize=10)
    fig.tight_layout(rect=(0, 0.01, 1, 0.9), h_pad=5.4)
    save(fig, out, "model_comparison.png")


# ------------------------------------------------------------------------------------------
# 2. Paired differences with 95% intervals (a forest plot)
# ------------------------------------------------------------------------------------------
def fig_paired(out: Path) -> None:
    data = load("paired_comparison.json")
    rows = []
    for sim, sim_label in SIMS:
        for r in data[sim]:
            flip = 1 if r["higher_is_better"] else -1
            scale = 100.0  # percentage points; AUC also shown in points of AUC x 100
            lo, hi = r["ci95"]
            ci = sorted((lo * flip * scale, hi * flip * scale))
            rows.append((sim_label, r["measure"], r["mean_diff"] * flip * scale, ci, r["verdict"], r["better_runs"], r["runs"], r["higher_is_better"]))
    fig, ax = plt.subplots(figsize=(10.5, 7.6))
    y = 0
    ticks, labels, group_y = [], [], {}
    for sim_label in [s for _, s in SIMS]:
        group_y[sim_label] = y
        y += 0.8
        for sim, measure, mean, ci, verdict, better_runs, runs, higher in [r for r in rows if r[0] == sim_label]:
            color = {"better": GREEN, "worse": RED}.get(verdict, GREY)
            ax.plot(ci, [y, y], color=color, linewidth=3, solid_capstyle="round")
            ax.plot([mean], [y], "o", color=color, markersize=8, zorder=3)
            ticks.append(y)
            labels.append(measure.replace("Next-answer AUC", "Next-answer AUC (x100)"))
            tail = {"better": f"better in {better_runs} of {runs} runs", "worse": f"worse in {runs - better_runs} of {runs} runs",
                    "no clear difference": f"within noise (better in {better_runs} of {runs} runs)"}[verdict]
            ax.text(max(ci[1], mean) + 1.0, y, tail, va="center", fontsize=8.8, color=color)
            y += 1
        y += 0.8
    ax.axvline(0, color=INK, linewidth=1)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.invert_yaxis()
    for sim_label, gy in group_y.items():
        ax.text(-0.012, gy, sim_label, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=11, fontweight="bold", color=BLUE)
    ax.set_xlabel("Improvement over the baseline, in percentage points   (right of 0 = improved model is better)")
    ax.set_title("Run by run, the improved model is clearly better on 12 of 14 measures", fontsize=13.5, fontweight="bold", loc="left", pad=34)
    ax.text(0, 1.012, "Dot: mean difference across 5 runs. Line: 95% interval. Lower-is-better measures are flipped, so right is always good.",
            transform=ax.transAxes, fontsize=9, color=MUTED)
    ax.set_xlim(-6, 38)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#e6eaee", linewidth=0.8)
    ax.set_axisbelow(True)
    save(fig, out, "paired_differences.png")


# ------------------------------------------------------------------------------------------
# 3. Improvement ladder: what each change adds
# ------------------------------------------------------------------------------------------
def fig_ladder(out: Path) -> None:
    runs = load("model_comparison.json")
    panels = [("hidden_prereq_blocker_hit", "Hidden root cause found", True), ("recommendation_is_true_blocker", "Lesson is a real blocker", True),
              ("known_concept_recommended", "Lesson on a concept the learner knew", False), ("false_alarm_rate", "False alarms", False)]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.4))
    fig.suptitle("What each model change adds, one at a time", fontsize=14, fontweight="bold", y=0.995)
    fig.text(0.5, 0.945, "Mean of 5 runs. Each point adds one change to the previous one; the last point is the improved model.", ha="center", fontsize=9.5, color=MUTED)
    for ax, (key, label, higher) in zip(axes.flat, panels):
        series = {sim: [mean_over_runs(runs[sim], "diagnosis", name, key) for name, _ in STEPS] for sim, _ in SIMS}
        for (sim, sim_label), color, marker in zip(SIMS, (BLUE, COPPER), ("o", "s")):
            vals = series[sim]
            other = series[[s for s, _ in SIMS if s != sim][0]]
            ax.plot(range(len(STEPS)), vals, marker=marker, color=color, linewidth=2.2, markersize=7, label=sim_label)
            for xi, v in enumerate(vals):
                above = v >= other[xi]  # the higher of the two labels goes above its point, the lower one below
                ax.annotate(f"{v:.0f}", (xi, v), xytext=(0, 8 if above else -14), textcoords="offset points", ha="center", fontsize=8.5, color=color)
        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        ax.set_xticks(range(len(STEPS)))
        ax.set_xticklabels([lab for _, lab in STEPS], fontsize=8.2)
        ax.set_title(f"{label}  ({'higher' if higher else 'lower'} is better)", fontsize=10.5, fontweight="bold", loc="left")
        ax.set_ylabel("% of cases", fontsize=9)
        ax.grid(axis="y", color="#e6eaee")
        ax.set_axisbelow(True)
        ax.margins(y=0.18)
        if key == "hidden_prereq_blocker_hit":
            ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout(rect=(0, 0, 1, 0.93), h_pad=3)
    save(fig, out, "improvement_ladder.png")


# ------------------------------------------------------------------------------------------
# 4. BKT against plain accuracy
# ------------------------------------------------------------------------------------------
def fig_bkt_vs_accuracy(out: Path) -> None:
    data = load("accuracy_baseline.json")
    methods = [("Study what you got wrong (status quo)", "Study what you\ngot wrong", GREY_L), ("Accuracy + prerequisite walk", "Plain accuracy\n+ walk", BLUE),
               ("Baseline: BKT + prerequisite walk", "BKT baseline\n+ walk", GREY), (IMP, "BKT improved\n+ walk", COPPER)]
    measures = [("hidden_prereq_blocker_hit", "Hidden root\ncause found", True), ("recommendation_is_true_blocker", "Lesson is a\nreal blocker", True),
                ("known_concept_recommended", "Lesson on a concept\nthe learner knew", False), ("false_alarm_rate", "False alarms", False)]
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 8.6), sharex=False)
    fig.suptitle("Does knowledge tracing earn its place? Yes: with the same walk it finds far more real blockers", fontsize=13.5, fontweight="bold", y=0.995)
    fig.text(0.5, 0.955, "Same learners, same prerequisite walk, same 0.6 threshold. Only the estimate of what the learner knows differs. Mean of 5 runs.", ha="center", fontsize=9.5, color=MUTED)
    for ax, (sim, sim_label) in zip(axes, SIMS):
        x = np.arange(len(measures))
        w = 0.2
        for k, (name, lab, color) in enumerate(methods):
            vals = [mean_over_runs(data[sim], "", "", "") if False else statistics.fmean(r[name][m] for r in data[sim]) * 100 for m, _, _ in measures]
            bars = ax.bar(x + (k - 1.5) * w, vals, w, color=color, label=lab.replace("\n", " "))
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.0f}", ha="center", fontsize=8.5)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{lab}\n({'higher' if h else 'lower'} is better)" for _, lab, h in measures], fontsize=9)
        ax.set_ylim(0, 78)
        ax.set_ylabel("% of cases", fontsize=9)
        ax.set_title(sim_label, fontsize=11, fontweight="bold", loc="left", color=BLUE)
        ax.grid(axis="y", color="#e6eaee")
        ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in methods]
    fig.legend(handles, [" ".join(lab.split()) for _, lab, _ in methods], loc="upper center", bbox_to_anchor=(0.5, 0.93), ncol=4, frameon=False, fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.9), h_pad=2.5)
    save(fig, out, "bkt_vs_accuracy.png")


# ------------------------------------------------------------------------------------------
# 5. EdNet
# ------------------------------------------------------------------------------------------
def fig_ednet(out: Path) -> None:
    text = (RES / "model_comparison.md").read_text(encoding="utf8")
    block = text[text.index("## EdNet"):]
    rows = re.findall(r"^\| (Baseline[^|]*|Improved[^|]*|Reference[^|]*) \| ([0-9.]+) \| ([0-9.]+) \| ([0-9.]+) \| ([0-9.]+) \|", block, re.M)
    if len(rows) != 3:
        print("skipped ednet_prediction.png: no EdNet table in model_comparison.md")
        return
    names = ["Baseline\nBKT", "Improved\nmodel", "Per-question\naccuracy"]
    colors = [GREY, COPPER, BLUE]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.9), gridspec_kw={"width_ratios": [1.15, 1, 1]})
    fig.suptitle("On real student answers (EdNet), the improved model predicts the next answer far better", fontsize=13.5, fontweight="bold", y=1.02)

    ax = axes[0]
    auc = [float(r[1]) for r in rows]
    bars = ax.bar(range(3), auc, color=colors, width=0.62)
    for b, v in zip(bars, auc):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v:.3f}", ha="center", fontsize=11, fontweight="bold")
    ax.axhline(0.5, color=MUTED, linestyle="--", linewidth=1)
    ax.text(-0.45, 0.505, "chance (0.5)", fontsize=8.5, color=MUTED, ha="left", va="bottom")
    ax.set_ylim(0.45, 0.79)
    ax.set_xticks(range(3))
    ax.set_xticklabels(names, fontsize=9)
    ax.set_title("AUC (higher is better)", fontsize=10.5, fontweight="bold", loc="left")

    for ax, idx, title in ((axes[1], 3, "Log loss (lower is better)"), (axes[2], 4, "Error, RMSE (lower is better)")):
        vals = [float(r[idx]) for r in rows]
        bars = ax.bar(range(3), vals, color=colors, width=0.62)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=10, fontweight="bold")
        ax.set_ylim(0, max(vals) * 1.15)  # bars start at zero, so differences are not exaggerated
        ax.set_xticks(range(3))
        ax.set_xticklabels(names, fontsize=9)
        ax.set_title(title, fontsize=10.5, fontweight="bold", loc="left")

    fig.text(0.5, -0.04, "40,000 sampled EdNet students. EdNet has no prerequisite graph, so only first-tag credit and question difficulty can be tested here.",
             ha="center", fontsize=9, color=MUTED)
    fig.tight_layout()
    save(fig, out, "ednet_prediction.png")


# ------------------------------------------------------------------------------------------
# 6. Robustness
# ------------------------------------------------------------------------------------------
def fig_robustness(out: Path) -> None:
    seeds = load("robustness.json")
    conditions = list(seeds[0].keys())
    short = {"Correct tags and graph": "Clean", "10% of items mis-tagged": "10% questions\nmis-tagged", "25% of items mis-tagged": "25% questions\nmis-tagged",
             "3 prerequisite links missing": "3 prerequisite\nlinks missing", "3 wrong prerequisite links": "3 wrong links\nadded"}
    panels = [("recommendation_is_true_blocker", "Lesson is a real blocker", True), ("hidden_prereq_blocker_hit", "Hidden root cause found", True),
              ("false_alarm_rate", "False alarms", False), ("missed_gap_rate", "Missed gaps", False)]
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.6))
    fig.suptitle("What happens when the concept tags or the prerequisite graph are wrong", fontsize=14, fontweight="bold", y=0.995)
    fig.text(0.5, 0.945, "Learners in Barabari's quiz format. Mean of 5 runs. The improved model stays ahead on three measures but misses more gaps, especially with bad tags.",
             ha="center", fontsize=9.5, color=MUTED)
    for ax, (key, label, higher) in zip(axes.flat, panels):
        x = np.arange(len(conditions))
        w = 0.38
        for k, (model, lab, color) in enumerate((("baseline", "Baseline", GREY), ("improved", "Improved model", COPPER))):
            vals = [statistics.fmean(s[c][model][key] for s in seeds) * 100 for c in conditions]
            bars = ax.bar(x + (k - 0.5) * w, vals, w, color=color, label=lab)
            small = key == "missed_gap_rate"
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + (0.2 if small else 0.8), f"{v:.1f}" if small else f"{v:.0f}", ha="center", fontsize=8.2)
        ax.set_xticks(x)
        ax.set_xticklabels([short.get(c, c) for c in conditions], fontsize=8.2)
        ax.set_title(f"{label}  ({'higher' if higher else 'lower'} is better)", fontsize=10.5, fontweight="bold", loc="left")
        ax.set_ylabel("% of cases", fontsize=9)
        ax.margins(y=0.16)
        ax.grid(axis="y", color="#e6eaee")
        ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=GREY), plt.Rectangle((0, 0), 1, 1, color=COPPER)]
    fig.legend(handles, ["Baseline", "Improved model"], loc="upper center", bbox_to_anchor=(0.5, 0.925), ncol=2, frameon=False, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.9), h_pad=3)
    save(fig, out, "robustness.png")


# ------------------------------------------------------------------------------------------
# 7. Failure analysis
# ------------------------------------------------------------------------------------------
def fig_failure(out: Path) -> None:
    text = (RES / "failure_analysis.md").read_text(encoding="utf8")
    lines = [ln for ln in text.splitlines() if ln.startswith("| ")]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    table = {}
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if cells[0] != "Cases":
            table[cells[0]] = [float(c.strip("%")) for c in cells[1:]]
    wanted = [("Sprint 2 sim, baseline", "Older simulator\nbaseline"), ("Sprint 2 sim, improved", "Older simulator\nimproved"),
              ("Barabari sim, baseline", "Barabari format\nbaseline"), ("Barabari sim, improved", "Barabari format\nimproved")]
    cols = [header.index(h) - 1 for h, _ in wanted]
    cats = [("Found the true blocker", GREEN, "Found the real blocker"),
            ("Recommended a concept the learner actually knew", RED, "Lesson on a concept the learner knew"),
            ("Blocker was asked about but looked fine", "#d99a2b", "Blocker was asked about but looked fine"),
            ("Recommended a real gap, but the real blocker was further upstream", GREY, "Real gap, but not the deepest one")]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    left = np.zeros(len(wanted))
    ys = np.arange(len(wanted))[::-1]
    for key, color, lab in cats:
        vals = np.array([table[key][c] for c in cols])
        ax.barh(ys, vals, left=left, color=color, label=lab, height=0.62)
        for yv, l, v in zip(ys, left, vals):
            if v >= 6:
                ax.text(l + v / 2, yv, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        left += vals
    ax.set_yticks(ys)
    ax.set_yticklabels([lab for _, lab in wanted], fontsize=9.5)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of hidden-prerequisite cases")
    ax.set_title("In the hardest cases the improved model finds the real blocker more often and wastes fewer lessons", fontsize=13, fontweight="bold", loc="left", pad=28)
    ax.text(0, 1.04, "A hidden-prerequisite case: the learner's real gap is a prerequisite of the concept the quick check showed (seed 0). Remaining share: no gap seen.",
            transform=ax.transAxes, fontsize=9, color=MUTED)
    ax.legend(frameon=False, fontsize=8.8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.17))
    save(fig, out, "failure_analysis.png")


# ------------------------------------------------------------------------------------------
# 8. What the tests cover
# ------------------------------------------------------------------------------------------
BACKEND_AREAS = [
    ("test_bkt", "Knowledge tracing"), ("test_model", "Models and question types"), ("test_diagnosis", "Gap and root cause"), ("test_engine", "Gap and root cause"),
    ("test_edge_cases", "Edge cases"), ("test_api", "API and contract"), ("test_contract", "API and contract"), ("test_parity", "API and contract"),
    ("test_storage", "Storage and safe retries"), ("test_security", "Security and limits"), ("test_barabari", "Barabari format"),
    ("test_simulate", "Simulator and data"), ("test_dataset", "Simulator and data"), ("test_evaluation", "Evaluation reports"), ("test_paired", "Evaluation reports"),
    ("test_accuracy_engine", "Evaluation reports"), ("test_shipped_params", "Evaluation reports"), ("test_plots", "Evaluation reports"),
]


def backend_counts() -> Counter:
    try:
        res = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT, capture_output=True, text=True, timeout=180)
    except Exception:
        return Counter()
    counts: Counter = Counter()
    for ln in res.stdout.splitlines():
        m = re.match(r"tests[\\/](\w+)\.py::", ln)
        if m:
            area = next((a for prefix, a in BACKEND_AREAS if m.group(1) == prefix), "Other")
            counts[area] += 1
    return counts


def frontend_counts() -> Counter:
    app = ROOT.parent / "frontend"
    if not (app / "package.json").exists():
        return Counter()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "vitest.json"
            subprocess.run(f'npx vitest run --reporter=json --outputFile="{report}"', cwd=app, capture_output=True, text=True, timeout=240, shell=True)
            data = json.loads(report.read_text(encoding="utf8"))
    except Exception:
        return Counter()
    names = {"engineClient": "Service connection and fallback", "journey": "Whole learner journey", "presets": "Demo scenarios", "marking": "Trainer marking",
             "engine": "Browser engine", "figures": "Accessibility", "listen": "Listen button"}
    counts: Counter = Counter()
    for f in data.get("testResults", []):
        stem = Path(f["name"]).name.split(".")[0]
        counts[names.get(stem, stem)] += sum(1 for t in f["assertionResults"] if t["status"] in ("passed", "skipped", "pending"))
    return counts


def fig_tests(out: Path) -> None:
    be, fe = backend_counts(), frontend_counts()
    if not be:
        print("skipped test_coverage.png: pytest could not collect the tests")
        return
    groups = [("Engine service (pytest)", be, BLUE)]
    if fe:
        groups.append(("App (vitest)", fe, COPPER))
    fig, axes = plt.subplots(1, len(groups), figsize=(11.5, 5.0), gridspec_kw={"width_ratios": [max(sum(c.values()), 30) for _, c, _ in groups]})
    axes = np.atleast_1d(axes)
    total = sum(sum(c.values()) for _, c, _ in groups)
    fig.suptitle(f"{total} automated tests, by what they protect", fontsize=14, fontweight="bold", y=1.02)
    for ax, (title, counts, color) in zip(axes, groups):
        items = sorted(counts.items(), key=lambda kv: kv[1])
        ax.barh([k for k, _ in items], [v for _, v in items], color=color, height=0.65)
        for yi, (_, v) in enumerate(items):
            ax.text(v + max(counts.values()) * 0.012, yi, str(v), va="center", fontsize=9.5, fontweight="bold")
        ax.set_title(f"{title}: {sum(counts.values())}", fontsize=11, fontweight="bold", loc="left", color=color)
        ax.set_xlim(0, max(counts.values()) * 1.18)
        ax.tick_params(axis="y", labelsize=9)
        ax.spines["bottom"].set_visible(False)
        ax.set_xticks([])
    fig.tight_layout()
    save(fig, out, "test_coverage.png")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(RES), help="folder for the PNG files")
    ap.add_argument("--skip-tests-figure", action="store_true", help="do not run pytest and vitest to count tests")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for fn in (fig_model_comparison, fig_paired, fig_ladder, fig_bkt_vs_accuracy, fig_ednet, fig_robustness, fig_failure):
        fn(out)
    if not args.skip_tests_figure:
        fig_tests(out)


if __name__ == "__main__":
    main()
