"""Compare the Sprint 3 model with the Sprint 2 baseline (PLAN S3-2 to S3-7).

    python scripts/compare_models.py [--learners 3000] [--seeds 5] [--write-service-params]

Runs both simulators (Sprint 2 and Barabari's quiz format) on the evaluation seeds 0 to 4 and
adds the model changes one at a time: first-tag credit, question difficulty, prerequisite-aware
learning, then more evidence before a lesson (the full improved model). The improved model's
settings were chosen on a separate tuning seed (100), never on these seeds.

Writes results/model_comparison.json and .md, and the first-tag parameters (fitted on the Sprint 2
simulator's seed 0 training learners, like the baseline's) to results/fitted_params_first_tag.json.
With `--write-service-params` they also replace the improved model's `concepts_first_tag` section
in circuit_coach/fitted_params.json; without it the service's shipped parameters are untouched.
If the EdNet files are present (see README) it also compares the two predictors on EdNet.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from circuit_coach import bkt, prediction
from circuit_coach.curriculum import CONCEPT_ORDER, CONCEPTS
from circuit_coach.diagnosis_eval import evaluate_diagnosis
from circuit_coach.engine import BASELINE, IMPROVED, Engine, ModelOptions
from circuit_coach.simulate import SimConfig, simulate

ROOT = Path(__file__).resolve().parents[1]
PREREQS = {c: d["prereqs"] for c, d in CONCEPTS.items()}

PREDICTORS = {
    "Baseline: BKT, fitted": lambda: prediction.BKTPredictor(),
    "+ first-tag credit": lambda: prediction.BKTPredictor(max_tags=1),
    "+ question difficulty": lambda: prediction.BKTPredictor(max_tags=1, item_difficulty=True),
    "Improved: + prerequisite-aware learning": lambda: prediction.BKTPredictor(
        max_tags=1, item_difficulty=True, prereqs=PREREQS, prereq_learn_factor=IMPROVED.prereq_learn_factor
    ),
    "Reference: per-question accuracy": lambda: prediction.ItemMean(),
}

STEPS = {
    "Baseline: BKT + prerequisite walk": BASELINE,
    "+ first-tag credit": ModelOptions("s1", credit="first"),
    "+ question difficulty": ModelOptions("s2", credit="first", item_difficulty=True),
    "+ prerequisite-aware learning": ModelOptions("s3", credit="first", item_difficulty=True, prereq_learn_factor=IMPROVED.prereq_learn_factor),
    "Improved: + more evidence before a lesson": IMPROVED,
}

DIAG_KEYS = [
    ("gap_f1", "Gap F1", True),
    ("recommendation_is_true_blocker", "True blocker", True),
    ("hidden_prereq_blocker_hit", "Hidden blocker found", True),
    ("known_concept_recommended", "Recommended a known concept", False),
    ("missed_gap_rate", "Missed gaps", False),
    ("false_alarm_rate", "False alarms", False),
]


def to_seqs(learners):
    return [[(r.item_id, r.concepts, int(r.correct), r.unsure, r.question_type, r.score, r.attempt) for r in lr.responses] for lr in learners]


def run_seed(sim: str, seed: int, n: int) -> dict:
    learners, _ = simulate(n, seed, SimConfig.named(sim))
    cut = int(0.7 * n)
    train, test = learners[:cut], learners[cut:]
    tr, te = to_seqs(train), to_seqs(test)

    pred, fitted = {}, {}
    for name, make in PREDICTORS.items():
        m = make().fit(tr)
        pred[name] = prediction.evaluate(m, te, skip_first=3)
        fitted[name] = m
    p_all = {c: fitted["Baseline: BKT, fitted"].params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}
    p_first = {c: fitted["+ first-tag credit"].params.get(c, bkt.HAND_SET) for c in CONCEPT_ORDER}
    difficulty = fitted["+ question difficulty"].difficulty

    engines = {
        name: Engine(p_all if opt.credit == "all" else p_first, options=opt, item_difficulty=difficulty) for name, opt in STEPS.items()
    }
    diag = {}
    for name, eng in engines.items():
        d = evaluate_diagnosis(test, None, {name: eng})[name]
        d["known_concept_recommended"] = 1 - d["recommendation_is_unmastered"]
        diag[name] = d
    return {
        "sim": sim,
        "seed": seed,
        "prediction": pred,
        "diagnosis": diag,
        "mean_slip": {"all_tags": float(np.mean([p.p_slip for p in p_all.values()])), "first_tag": float(np.mean([p.p_slip for p in p_first.values()]))},
        "params_first_tag": {c: p.as_dict() for c, p in p_first.items()},
    }


def stat(runs, *path) -> tuple[float, float]:
    vals = []
    for r in runs:
        v = r
        for k in path:
            v = v[k]
        vals.append(v)
    return float(np.mean(vals)), float(np.std(vals))


def fmt(m, s, pct=False):
    return f"{m * 100:.1f}% ± {s * 100:.1f}" if pct else f"{m:.3f} ± {s:.3f}"


def ednet_section(seed: int = 0) -> list[str]:
    raw = ROOT / "data" / "raw"
    if not (raw / "ednet_kt1.zip").exists():
        return ["", "## EdNet", "", "Not run: the EdNet files are not in `backend/data/raw/` (see README). The promotion check below needs this comparison."]
    from circuit_coach.ednet import load_sample

    seqs = load_sample(raw / "ednet_kt1.zip", raw / "contents" / "questions.csv", n_users=40000, seed=seed, cache=ROOT / "data" / "processed" / f"ednet_40000_{seed}.pkl")
    order = np.random.default_rng(seed).permutation(len(seqs))
    cut = int(0.8 * len(seqs))
    train, test = [seqs[i] for i in order[:cut]], [seqs[i] for i in order[cut:]]
    fast = dict(max_fit_sequences=3000, max_fit_len=100, n_random_starts=1)
    models = {
        "Baseline: BKT, fitted (all tags)": prediction.BKTPredictor(**fast),
        "Improved: first tag + question difficulty": prediction.BKTPredictor(max_tags=1, item_difficulty=True, **fast),
        "Reference: per-question accuracy": prediction.ItemMean(),
    }
    lines = ["", "## EdNet (real answers, no prerequisite graph)", "", "| Model | AUC | Accuracy | Log loss | RMSE |", "|---|---|---|---|---|"]
    for name, m in models.items():
        r = prediction.evaluate(m.fit(train), test, skip_first=5)
        lines.append(f"| {name} | {r['auc']:.3f} | {r['accuracy']:.3f} | {r['log_loss']:.3f} | {r['rmse']:.3f} |")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--learners", type=int, default=3000)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--write-service-params", action="store_true", help="also replace the improved model's parameters the service ships with")
    args = ap.parse_args()

    t0 = time.time()
    all_runs: dict[str, list[dict]] = {}
    for sim in ("sprint2", "barabari"):
        all_runs[sim] = []
        for seed in range(args.seeds):
            all_runs[sim].append(run_seed(sim, seed, args.learners))
            print(f"{sim} seed {seed} done ({time.time() - t0:.0f}s)", flush=True)

    # First-tag parameters for the improved model, from the same data as the baseline's. They go
    # to results/; the service's shipped file changes only on request.
    (ROOT / "results").mkdir(exist_ok=True)
    first_tag = all_runs["sprint2"][0]["params_first_tag"]
    (ROOT / "results" / "fitted_params_first_tag.json").write_text(
        json.dumps({"concepts_first_tag": first_tag}, indent=2) + "\n", encoding="utf8"
    )
    if args.write_service_params:
        params_file = ROOT / "circuit_coach" / "fitted_params.json"
        params = json.loads(params_file.read_text(encoding="utf8"))
        params["concepts_first_tag"] = first_tag
        params_file.write_text(json.dumps(params, indent=2) + "\n", encoding="utf8")
        print(f"updated {params_file}")
    (ROOT / "results" / "model_comparison.json").write_text(json.dumps(all_runs, indent=1) + "\n", encoding="utf8")

    lines = [
        "# Sprint 3 model against the Sprint 2 baseline",
        "",
        f"{args.seeds} runs of {args.learners} made-up learners per simulator (70% train, 30% test), evaluation seeds 0 to {args.seeds - 1}. Mean ± standard deviation across runs. The improved model's settings were chosen on tuning seed 100.",
        "",
        f"Improved model: first-tag credit, question difficulty, prerequisite-aware learning (factor {IMPROVED.prereq_learn_factor}), and a lesson only after {IMPROVED.min_evidence} answers on the concept unless its mastery is below {IMPROVED.strong_evidence}.",
    ]
    checks = []
    for sim, label in (("sprint2", "Sprint 2 simulator"), ("barabari", "Barabari's quiz format")):
        runs = all_runs[sim]
        lines += ["", f"## {label}", "", "### Predicting the next answer", "", "| Model | AUC | Accuracy | Log loss | RMSE |", "|---|---|---|---|---|"]
        for name in PREDICTORS:
            lines.append(f"| {name} | " + " | ".join(fmt(*stat(runs, "prediction", name, k)) for k in ("auc", "accuracy", "log_loss", "rmse")) + " |")
        ms_all, ms_first = stat(runs, "mean_slip", "all_tags"), stat(runs, "mean_slip", "first_tag")
        lines += ["", f"Mean fitted slip: {fmt(*ms_all)} with every tag, {fmt(*ms_first)} with first-tag credit (true slip in the simulator 0.04 to 0.14, mean about 0.09).", ""]
        lines += ["### Finding the gap and the lesson", "", "| Model | " + " | ".join(h for _, h, _ in DIAG_KEYS) + " |", "|---|" + "---|" * len(DIAG_KEYS)]
        for name in STEPS:
            lines.append(f"| {name} | " + " | ".join(fmt(*stat(runs, "diagnosis", name, k), pct=True) for k, _, _ in DIAG_KEYS) + " |")
        base, imp = "Baseline: BKT + prerequisite walk", "Improved: + more evidence before a lesson"
        for k, h, higher in DIAG_KEYS:
            b, i = stat(runs, "diagnosis", base, k)[0], stat(runs, "diagnosis", imp, k)[0]
            checks.append((label, h, b, i, (i > b) if higher else (i < b)))
        b, i = stat(runs, "prediction", "Baseline: BKT, fitted", "auc")[0], stat(runs, "prediction", "Improved: + prerequisite-aware learning", "auc")[0]
        checks.append((label, "Next-answer AUC", b, i, i > b))

    lines += ednet_section()
    lines += ["", "## Promotion check (made-up learners)", "", "| Data | Measure | Baseline | Improved | Better |", "|---|---|---|---|---|"]
    for label, h, b, i, ok in checks:
        f = (lambda x: f"{x:.3f}") if h == "Next-answer AUC" else (lambda x: f"{x * 100:.1f}%")
        lines.append(f"| {label} | {h} | {f(b)} | {f(i)} | {'yes' if ok else 'no'} |")
    (ROOT / "results" / "model_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines))
    print(f"total {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
