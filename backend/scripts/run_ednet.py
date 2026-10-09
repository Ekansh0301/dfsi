"""Check the baseline on real data: does BKT predict real students' next answers?

    python scripts/run_ednet.py [--users 40000]

Needs data/raw/ednet_kt1.zip and data/raw/contents/questions.csv (see backend/README.md).
Writes results/ednet_results.json and results/ednet_results.md.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from circuit_coach import prediction
from circuit_coach.ednet import load_sample

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=40000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    t0 = time.time()
    seqs = load_sample(RAW / "ednet_kt1.zip", RAW / "contents" / "questions.csv", n_users=args.users, seed=args.seed, cache=ROOT / "data" / "processed" / f"ednet_{args.users}_{args.seed}.pkl")
    print(f"{len(seqs)} students kept ({time.time() - t0:.0f}s)", flush=True)

    rng = np.random.default_rng(args.seed)
    order = rng.permutation(len(seqs))
    cut = int(0.8 * len(seqs))
    train = [seqs[i] for i in order[:cut]]
    test = [seqs[i] for i in order[cut:]]
    n_answers = sum(len(s) for s in test)
    all_tags = {c for s in seqs for _, tags, _, _ in s for c in tags}
    print(f"train {len(train)} students, test {len(test)} students ({n_answers} test answers), {len(all_tags)} concept tags", flush=True)

    fast = dict(max_fit_sequences=3000, max_fit_len=100, n_random_starts=1)
    models = [
        prediction.GlobalMean(),
        prediction.ItemMean(),
        prediction.RunningAccuracy(),
        prediction.BKTPredictor(fit_params=False, name="BKT (hand-set parameters)"),
        prediction.BKTPredictor(fit_params=True, name="BKT (fitted, all tags)", **fast),
        prediction.BKTPredictor(fit_params=True, name="BKT (fitted, first tag only)", max_tags=1, **fast),
    ]
    results = {}
    for m in models:
        t = time.time()
        m.fit(train)
        results[m.name] = prediction.evaluate(m, test, skip_first=5)
        print(f"{m.name}: AUC {results[m.name]['auc']:.3f} ({time.time() - t:.0f}s)", flush=True)

    info = {"students_kept": len(seqs), "train_students": len(train), "test_students": len(test), "test_answers": n_answers, "concept_tags": len(all_tags)}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "ednet_results.json").write_text(json.dumps({"info": info, "results": results}, indent=1) + "\n")
    lines = [
        "# Baseline check on real data (EdNet KT1)",
        "",
        f"{info['students_kept']:,} randomly sampled students with at least 30 answers (first 300 kept). 80% train, 20% test: {info['test_students']:,} students, {info['test_answers']:,} test answers. {info['concept_tags']} concept tags.",
        "",
        "| Method | AUC | Accuracy | Log loss | RMSE |",
        "|---|---|---|---|---|",
    ]
    for name, r in results.items():
        lines.append(f"| {name} | {r['auc']:.3f} | {r['accuracy']:.3f} | {r['log_loss']:.3f} | {r['rmse']:.3f} |")
    (ROOT / "results" / "ednet_results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
