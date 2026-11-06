"""Robustness of the engine (PLAN S4-2).

    python scripts/robustness.py [--learners 3000] [--seeds 3]

1. Parameter stability: how much the fitted BKT parameters move across the 5 evaluation seeds,
   and how often they sit on a fitting bound (read from the saved result files).
2. Noisy concept tags: the engine, and the fit, see items whose main tag was swapped for a random
   other concept (10% and 25% of items), as could happen with unit-level tags in Barabari's data.
3. Wrong concept graph: the engine walks a graph with three real prerequisite links missing, or
   with three wrong links added. The hidden truth always uses the real graph.

Made-up learners with Barabari's quiz format; baseline and improved model. Writes
results/robustness.md and .json.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from circuit_coach import bkt, prediction
from circuit_coach.bkt import BOUNDS
from circuit_coach.curriculum import CONCEPT_ORDER, CONCEPTS
from circuit_coach.diagnosis_eval import evaluate_diagnosis
from circuit_coach.engine import BASELINE, IMPROVED, Engine
from circuit_coach.simulate import SimConfig, SimLearner, simulate

ROOT = Path(__file__).resolve().parents[1]
TRUE_GRAPH = {c: list(d["prereqs"]) for c, d in CONCEPTS.items()}
MISSING = [("diagrams", "symbols"), ("fault", "diagrams"), ("series_parallel", "ohm")]  # (concept, prerequisite) removed
WRONG = [("symbols", "multimeter"), ("earthing", "ohm"), ("diagrams", "ohm")]  # added, not in the real graph
KEYS = [
    ("recommendation_is_true_blocker", "True blocker", True),
    ("hidden_prereq_blocker_hit", "Hidden blocker found", True),
    ("missed_gap_rate", "Missed gaps", False),
    ("false_alarm_rate", "False alarms", False),
]


def graph_without(edges):
    g = {c: list(p) for c, p in TRUE_GRAPH.items()}
    for c, p in edges:
        g[c].remove(p)
    return g


def graph_with(edges):
    g = {c: list(p) for c, p in TRUE_GRAPH.items()}
    for c, p in edges:
        g[c].append(p)
    return g


def noisy_tags(learners: list[SimLearner], bank, share: float, seed: int) -> list[SimLearner]:
    """Copies of the learners whose items carry a wrong main tag for `share` of the items."""
    rng = np.random.default_rng(seed + 777)
    swap = {}
    for items in bank.values():
        for it in items:
            if rng.random() < share:
                wrong = str(rng.choice([c for c in CONCEPT_ORDER if c != it.concepts[0]]))
                swap[it.id] = (wrong, *it.concepts[1:])
    out = []
    for lr in learners:
        resp = [replace(r, concepts=swap.get(r.item_id, r.concepts)) for r in lr.responses]
        out.append(SimLearner(lr.id, lr.experience, resp, lr.assess_points))
    return out, len(swap) / sum(len(v) for v in bank.values())


def to_seqs(learners):
    return [[(r.item_id, r.concepts, int(r.correct), r.unsure, r.question_type, r.score, r.attempt) for r in lr.responses] for lr in learners]


def engines(train, graph):
    tr = to_seqs(train)
    base = prediction.BKTPredictor().fit(tr)
    first = prediction.BKTPredictor(max_tags=1, item_difficulty=True).fit(tr)
    p_all = {c: base.params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}
    p_first = {c: first.params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}
    return {
        "baseline": Engine(p_all, options=BASELINE, prereqs=graph),
        "improved": Engine(p_first, options=IMPROVED, item_difficulty=first.difficulty, prereqs=graph),
    }


def run_seed(seed: int, n: int) -> dict:
    learners, bank = simulate(n, seed, SimConfig())
    cut = int(0.7 * n)
    out = {}
    conditions = {
        "Correct tags and graph": (0.0, TRUE_GRAPH),
        "10% of items mis-tagged": (0.10, TRUE_GRAPH),
        "25% of items mis-tagged": (0.25, TRUE_GRAPH),
        "3 prerequisite links missing": (0.0, graph_without(MISSING)),
        "3 wrong prerequisite links": (0.0, graph_with(WRONG)),
    }
    for name, (share, graph) in conditions.items():
        seen = learners
        if share:
            seen, _ = noisy_tags(learners, bank, share, seed)
        train, test_seen = seen[:cut], seen[cut:]
        test_truth = learners[cut:]
        res = {}
        for model, eng in engines(train, graph).items():
            # The engine sees the (possibly noisy) tags; truth comes from the real learners.
            mixed = [SimLearner(t.id, t.experience, s.responses, t.assess_points) for s, t in zip(test_seen, test_truth)]
            res[model] = evaluate_diagnosis(mixed, None, {model: eng})[model]
        out[name] = res
    return out


def param_stability() -> list[str]:
    lines = ["## 1. Fitted parameters across the 5 evaluation seeds", "", "Standard deviation across seeds, averaged over the 10 concepts, and the share of fitted values on a fitting bound.", ""]
    lines += ["| Simulator | Fit | p_init | p_learn | p_slip | p_guess | On a bound |", "|---|---|---|---|---|---|---|"]
    comp = json.loads((ROOT / "results" / "model_comparison.json").read_text(encoding="utf8"))
    sources = {
        "Sprint 2": [r["fitted_params"] for r in json.loads((ROOT / "results" / "synthetic_results.json").read_text(encoding="utf8"))],
        "Barabari": [r["fitted_params"] for r in json.loads((ROOT / "results" / "synthetic_barabari_results.json").read_text(encoding="utf8"))],
    }
    first = {"Sprint 2": [r["params_first_tag"] for r in comp["sprint2"]], "Barabari": [r["params_first_tag"] for r in comp["barabari"]]}
    for sim in ("Sprint 2", "Barabari"):
        for fit, runs in (("every tag (baseline)", sources[sim]), ("first tag (improved)", first[sim])):
            sds, on_bound, total = [], 0, 0
            for k in ("p_init", "p_learn", "p_slip", "p_guess"):
                vals = np.array([[r[c][k] for c in CONCEPT_ORDER] for r in runs])
                sds.append(float(vals.std(axis=0).mean()))
                lo, hi = BOUNDS[k]
                on_bound += int(((vals <= lo + 1e-3) | (vals >= hi - 1e-3)).sum())
                total += vals.size
            lines.append(f"| {sim} | {fit} | " + " | ".join(f"{x:.3f}" for x in sds) + f" | {on_bound / total * 100:.0f}% |")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--learners", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()
    t0 = time.time()
    runs = []
    for seed in range(args.seeds):
        runs.append(run_seed(seed, args.learners))
        print(f"seed {seed} done ({time.time() - t0:.0f}s)", flush=True)
    (ROOT / "results" / "robustness.json").write_text(json.dumps(runs, indent=1) + "\n", encoding="utf8")

    lines = [
        "# Robustness of the engine",
        "",
        f"Made-up learners with Barabari's quiz format: {args.seeds} runs of {args.learners} (seeds 0 to {args.seeds - 1}), 70% train, 30% test. Mean ± standard deviation across runs.",
        "",
    ]
    lines += param_stability()
    lines += [
        "",
        "## 2. Wrong concept tags and a wrong concept graph",
        "",
        "Mis-tagged items swap their main tag for a random other concept, in the data the model is fitted and traced on. "
        f"Missing links: {', '.join(f'{p} before {c}' for c, p in MISSING)}. Wrong links added: {', '.join(f'{p} before {c}' for c, p in WRONG)}. "
        "The hidden truth always uses the real graph.",
        "",
        "| Condition | Model | " + " | ".join(h for _, h, _ in KEYS) + " |",
        "|---|---|" + "---|" * len(KEYS),
    ]
    for cond in runs[0]:
        for model in ("baseline", "improved"):
            cells = []
            for k, _, _ in KEYS:
                v = np.array([r[cond][model][k] for r in runs])
                cells.append(f"{v.mean() * 100:.1f}% ± {v.std() * 100:.1f}")
            lines.append(f"| {cond} | {model} | " + " | ".join(cells) + " |")
    lines += ["", "## 3. Change from the clean condition (improved model)", "", "| Condition | " + " | ".join(h for _, h, _ in KEYS) + " |", "|---|" + "---|" * len(KEYS)]
    clean = {k: np.mean([r["Correct tags and graph"]["improved"][k] for r in runs]) for k, _, _ in KEYS}
    for cond in list(runs[0])[1:]:
        cells = [f"{(np.mean([r[cond]['improved'][k] for r in runs]) - clean[k]) * 100:+.1f} points" for k, _, _ in KEYS]
        lines.append(f"| {cond} | " + " | ".join(cells) + " |")
    (ROOT / "results" / "robustness.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines))
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
