"""Estimate per-question difficulty from the answers the service has stored.

    python scripts/estimate_item_difficulty.py --db sqlite:///circuit_coach.db
    python scripts/estimate_item_difficulty.py --db postgresql://... --write-service-table

A question answered right less often than its main concept is harder (positive shift on the
logit scale); rates are shrunk towards the concept's rate, so a question with few answers stays
near 0 (`prediction.estimate_item_difficulty`, the estimator evaluated in `results/model_comparison.md`).
Only first attempts count, so retakes do not make a question look easy.

Without `--write-service-table` the table goes to `results/item_difficulty.json` only. With it,
the table the service ships (`circuit_coach/item_difficulty.json`) and the copy the browser
engine carries (`frontend/src/data/itemDifficulty.json`) are both rewritten.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from circuit_coach import barabari, prediction
from circuit_coach.storage import Storage

ROOT = Path(__file__).resolve().parents[1]
SERVICE_TABLE = ROOT / "circuit_coach" / "item_difficulty.json"
BROWSER_TABLE = ROOT.parent / "frontend" / "src" / "data" / "itemDifficulty.json"
REPORT = ROOT / "results" / "item_difficulty.json"
SOURCE = "Per-question difficulty on the logit scale, estimated from stored answers by scripts/estimate_item_difficulty.py. Questions not listed count as average (0)."


def answers_of(step: dict) -> list[tuple[str, tuple[str, ...], int]]:
    """(question id, concept tags, right or wrong) for each first-attempt answer in a logged step."""
    req, kind = step["request"], step["step"]
    out: list[tuple[str, tuple[str, ...], int]] = []
    if kind in ("onboarding", "quiz-result"):
        for e in req.get("events", []):
            if e.get("item_id") and e.get("attempt_number", 1) == 1:
                out.append((e["item_id"], tuple(e["concept_tags"]), int(e.get("is_correct", False))))
    elif kind == "marked-answer":
        if req.get("item_id") and req.get("attempt_number", 1) == 1:
            out.append((req["item_id"], tuple(req["concept_tags"]), int(req["score"] >= 0.5)))
    elif kind == "barabari-quiz-attempt":
        quiz, attempt = barabari.parse_quiz(req["quiz"]), barabari.parse_attempt(req["attempt"])
        tags = barabari.TagMap.from_dict(req["tags"]) if req.get("tags") else barabari.TagMap.load()
        for ev in barabari.attempt_events(quiz, attempt, tags):
            if ev.item_id and ev.attempt_number == 1:
                out.append((ev.item_id, ev.concept_tags, int(ev.is_correct)))
    return out


def estimate(steps: list[dict], shrink: float = 5.0) -> dict[str, float]:
    by_learner: dict[str, list] = {}
    for st in steps:
        by_learner.setdefault(st["learner_id"], []).extend(answers_of(st))
    train = [seq for seq in by_learner.values() if seq]
    table = prediction.estimate_item_difficulty(train, shrink=shrink)
    return {q: round(v, 4) for q, v in sorted(table.items())}


def write(path: Path, table: dict[str, float]) -> None:
    path.write_text(json.dumps({"source": SOURCE, "items": table}, indent=2) + "\n", encoding="utf8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.environ.get("CIRCUIT_COACH_DB"), help="database URL (default: CIRCUIT_COACH_DB)")
    ap.add_argument("--shrink", type=float, default=5.0, help="pseudo-answers pulling a question towards its concept's rate")
    ap.add_argument("--write-service-table", action="store_true", help="rewrite the tables the service and the browser ship")
    args = ap.parse_args()
    if not args.db:
        raise SystemExit("Give --db or set CIRCUIT_COACH_DB")
    table = estimate(Storage(args.db).steps(), args.shrink)
    write(REPORT, table)
    print(f"{len(table)} questions estimated, wrote {REPORT}")
    if args.write_service_table:
        write(SERVICE_TABLE, table)
        write(BROWSER_TABLE, table)
        print(f"wrote {SERVICE_TABLE} and {BROWSER_TABLE}")


if __name__ == "__main__":
    main()
