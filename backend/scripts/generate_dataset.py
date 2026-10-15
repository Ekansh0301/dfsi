"""Generate, save and validate a made-up learner dataset.

    python scripts/generate_dataset.py [--learners 500] [--seed 0] [--out datasets/synthetic_seed0]
    python scripts/generate_dataset.py --check datasets/synthetic_seed0

The same seed always gives byte-identical files. `--check` re-reads a saved dataset, verifies
its checksums and runs the validator.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from circuit_coach import dataset

ROOT = Path(__file__).resolve().parents[1]


def check(directory: Path) -> int:
    problems = dataset.verify_files(directory) + dataset.validate(dataset.load(directory))
    for p in problems[:20]:
        print("PROBLEM:", p)
    print("dataset OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--learners", type=int, default=500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--check", type=Path, default=None, help="validate an existing dataset directory and exit")
    args = ap.parse_args()
    if args.check:
        return check(args.check)

    out = args.out or ROOT / "datasets" / f"synthetic_seed{args.seed}"
    ds = dataset.generate(args.learners, args.seed)
    problems = dataset.validate(ds)
    if problems:
        print("\n".join(problems[:20]))
        return 1
    m = dataset.save(ds, out)
    print(f"wrote {out}: {m['n_learners']} learners ({m['split']['train']} train, {m['split']['test']} test), {m['n_responses']} answers")
    return check(out)


if __name__ == "__main__":
    sys.exit(main())
