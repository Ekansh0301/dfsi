"""Save, load and validate the made-up learner datasets (Issue T5).

`simulate.py` generates learners in memory. This module turns a run into files that can be
committed and re-read, keeps the hidden ground truth next to the answers, splits learners
70:30 into train and test, and checks that a dataset is internally consistent.

Files written to one directory:

    items.csv         item_id, concepts (joined with "|"), slip, guess
    learners.csv      learner_id, experience, split ("train" or "test"), n_responses
    responses.csv     learner_id, step, item_id, concepts, correct, unsure, module
    ground_truth.csv  learner_id, module, n_responses, assessed, <one 0/1 column per concept>
    manifest.json     seed, sizes, split, checksums of the other files
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .curriculum import CONCEPT_ORDER, CONCEPTS, MODULES
from .simulate import AssessPoint, Item, Response, SimLearner, simulate

TRAIN_SHARE = 0.7
FILES = ("items.csv", "learners.csv", "responses.csv", "ground_truth.csv")


@dataclass
class Dataset:
    learners: list[SimLearner]
    bank: dict[str, list[Item]]
    split: dict[int, str]  # learner id -> "train" or "test"
    seed: int

    @property
    def train(self) -> list[SimLearner]:
        return [lr for lr in self.learners if self.split[lr.id] == "train"]

    @property
    def test(self) -> list[SimLearner]:
        return [lr for lr in self.learners if self.split[lr.id] == "test"]


def split_learners(n: int, seed: int, train_share: float = TRAIN_SHARE) -> dict[int, str]:
    """Random but reproducible split by learner, so no learner is in both parts."""
    order = np.random.default_rng(seed + 10_000).permutation(n)
    n_train = int(round(train_share * n))
    train = set(int(i) for i in order[:n_train])
    return {i: ("train" if i in train else "test") for i in range(n)}


def generate(n_learners: int, seed: int = 0) -> Dataset:
    learners, bank = simulate(n_learners, seed)
    return Dataset(learners, bank, split_learners(len(learners), seed), seed)


# ---- writing -----------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, header: list[str], rows) -> None:
    with path.open("w", newline="", encoding="utf8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def save(ds: Dataset, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    items = [i for c in CONCEPT_ORDER for i in ds.bank[c]]
    _write_csv(out / "items.csv", ["item_id", "concepts", "slip", "guess"], ([i.id, "|".join(i.concepts), f"{i.slip:.4f}", f"{i.guess:.4f}"] for i in items))
    _write_csv(
        out / "learners.csv",
        ["learner_id", "experience", "split", "n_responses"],
        ([lr.id, lr.experience, ds.split[lr.id], len(lr.responses)] for lr in ds.learners),
    )
    _write_csv(
        out / "responses.csv",
        ["learner_id", "step", "item_id", "concepts", "correct", "unsure", "module"],
        ([lr.id, k, r.item_id, "|".join(r.concepts), int(r.correct), int(r.unsure), r.module] for lr in ds.learners for k, r in enumerate(lr.responses)),
    )
    _write_csv(
        out / "ground_truth.csv",
        ["learner_id", "module", "n_responses", "assessed", *CONCEPT_ORDER],
        (
            [lr.id, ap.module, ap.n_responses, "|".join(ap.assessed), *(int(ap.truth[c]) for c in CONCEPT_ORDER)]
            for lr in ds.learners
            for ap in lr.assess_points
        ),
    )
    manifest = {
        "generator": "circuit_coach.simulate",
        "seed": ds.seed,
        "n_learners": len(ds.learners),
        "n_responses": sum(len(lr.responses) for lr in ds.learners),
        "split": {"train": len(ds.train), "test": len(ds.test), "train_share": TRAIN_SHARE},
        "concepts": CONCEPT_ORDER,
        "sha256": {name: _sha256(out / name) for name in FILES},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    return manifest


# ---- reading -----------------------------------------------------------------------------


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def load(directory: Path) -> Dataset:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf8"))
    bank: dict[str, list[Item]] = {c: [] for c in CONCEPT_ORDER}
    for row in _read(directory / "items.csv"):
        tags = tuple(row["concepts"].split("|"))
        bank[tags[0]].append(Item(row["item_id"], tags, float(row["slip"]), float(row["guess"])))
    learners: dict[int, SimLearner] = {}
    split: dict[int, str] = {}
    for row in _read(directory / "learners.csv"):
        lid = int(row["learner_id"])
        learners[lid] = SimLearner(lid, row["experience"])
        split[lid] = row["split"]
    for row in _read(directory / "responses.csv"):
        learners[int(row["learner_id"])].responses.append(
            Response(row["item_id"], tuple(row["concepts"].split("|")), bool(int(row["correct"])), bool(int(row["unsure"])), row["module"])
        )
    for row in _read(directory / "ground_truth.csv"):
        learners[int(row["learner_id"])].assess_points.append(
            AssessPoint(row["module"], int(row["n_responses"]), row["assessed"].split("|"), {c: bool(int(row[c])) for c in CONCEPT_ORDER})
        )
    return Dataset([learners[i] for i in sorted(learners)], bank, split, manifest["seed"])


# ---- validation --------------------------------------------------------------------------


def validate(ds: Dataset) -> list[str]:
    """Return a list of problems (empty when the dataset is consistent)."""
    problems: list[str] = []
    items = {i.id: i for bank in ds.bank.values() for i in bank}
    ids = [lr.id for lr in ds.learners]
    if len(set(ids)) != len(ids):
        problems.append("duplicate learner ids")
    if set(ds.split) != set(ids):
        problems.append("split does not cover exactly the learners")
    if set(ds.split.values()) - {"train", "test"}:
        problems.append("split has values other than train and test")
    if ds.learners:
        share = len(ds.train) / len(ds.learners)
        if abs(share - TRAIN_SHARE) > 1.0 / len(ds.learners) + 1e-9:
            problems.append(f"train share {share:.3f} is not {TRAIN_SHARE}")
    for it in items.values():
        if not set(it.concepts) <= set(CONCEPTS):
            problems.append(f"item {it.id} has an unknown concept")
        if not (0 < it.slip < 0.5 and 0 < it.guess < 0.5):
            problems.append(f"item {it.id} has slip or guess outside (0, 0.5)")
    for lr in ds.learners:
        if not lr.responses:
            problems.append(f"learner {lr.id} has no responses")
        if not lr.assess_points:
            problems.append(f"learner {lr.id} has no assessment points")
        for r in lr.responses:
            it = items.get(r.item_id)
            if it is None:
                problems.append(f"learner {lr.id}: unknown item {r.item_id}")
            elif r.concepts != it.concepts:
                problems.append(f"learner {lr.id}: concepts of {r.item_id} differ from the item bank")
            if r.unsure and r.correct:
                problems.append(f"learner {lr.id}: an unsure answer marked correct")
            if r.module not in MODULES:
                problems.append(f"learner {lr.id}: unknown module {r.module}")
        last = 0
        for ap in lr.assess_points:
            if ap.n_responses < last or ap.n_responses > len(lr.responses):
                problems.append(f"learner {lr.id}: assessment point at {ap.n_responses} responses is out of order")
            last = ap.n_responses
            if set(ap.truth) != set(CONCEPTS):
                problems.append(f"learner {lr.id}: ground truth does not cover every concept")
            if ap.module not in MODULES or ap.assessed != MODULES[ap.module]["concepts"]:
                problems.append(f"learner {lr.id}: assessed concepts do not match module {ap.module}")
    # The hidden state should mostly follow the prerequisites (a concept is rarely mastered while one is not).
    broken = total = 0
    for lr in ds.learners:
        for ap in lr.assess_points:
            for c, d in CONCEPTS.items():
                total += 1
                broken += ap.truth.get(c, False) and not all(ap.truth.get(p, False) for p in d["prereqs"])
    if total and broken / total > 0.10:
        problems.append(f"{broken / total:.1%} of hidden states have a mastered concept with an unmastered prerequisite")
    return problems


def verify_files(directory: Path) -> list[str]:
    """Check the saved files against the manifest checksums."""
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf8"))
    return [f"{name} does not match its checksum" for name, digest in manifest["sha256"].items() if _sha256(directory / name) != digest]
