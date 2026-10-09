"""Next-answer prediction: BKT against simple baselines.

Every predictor sees a learner's answers one at a time and, before each answer, outputs the
probability that it will be correct. This is the standard way to compare knowledge-tracing
models, and it works on any dataset of (learner, question, concept tags, correct) sequences.

The ladder of predictors, from simplest to our baseline model:

    GlobalMean       the overall correct rate (no learner, question or concept information)
    ItemMean         each question's own correct rate in the training data
    RunningAccuracy  the learner's own accuracy so far on the concepts tagged on the question
    BKTPredictor     per-concept Bayesian Knowledge Tracing (our baseline model)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

import numpy as np

from . import bkt
from .bkt import BKTParams

# One answer: (question id, concept tags, correct, "I'm not sure" chosen)
Step = tuple[str, tuple, int, bool]
Seq = Sequence[Step]


def _clip(p: float) -> float:
    return min(0.999, max(0.001, p))


class GlobalMean:
    name = "Global average"

    def fit(self, train: Iterable[Seq]) -> "GlobalMean":
        n = k = 0
        for seq in train:
            for _, _, y, _ in seq:
                n += 1
                k += y
        self.p = k / max(n, 1)
        return self

    def predict(self, seq: Seq) -> np.ndarray:
        return np.full(len(seq), self.p)


class ItemMean:
    name = "Per-question accuracy"

    def __init__(self, smoothing: float = 2.0):
        self.a = smoothing

    def fit(self, train: Iterable[Seq]) -> "ItemMean":
        n: dict[str, int] = defaultdict(int)
        k: dict[str, int] = defaultdict(int)
        tn = tk = 0
        for seq in train:
            for q, _, y, _ in seq:
                n[q] += 1
                k[q] += y
                tn += 1
                tk += y
        self.prior = tk / max(tn, 1)
        self.n, self.k = n, k
        return self

    def predict(self, seq: Seq) -> np.ndarray:
        return np.array(
            [_clip((self.k.get(q, 0) + self.a * self.prior) / (self.n.get(q, 0) + self.a)) for q, _, _, _ in seq]
        )


class RunningAccuracy:
    name = "Learner's running accuracy"

    def __init__(self, smoothing: float = 2.0):
        self.a = smoothing

    def fit(self, train: Iterable[Seq]) -> "RunningAccuracy":
        n = k = 0
        for seq in train:
            for _, _, y, _ in seq:
                n += 1
                k += y
        self.prior = k / max(n, 1)
        return self

    def predict(self, seq: Seq) -> np.ndarray:
        n: dict[str, int] = defaultdict(int)
        k: dict[str, int] = defaultdict(int)
        out = np.empty(len(seq))
        for i, (_, tags, y, _) in enumerate(seq):
            ps = [(k[c] + self.a * self.prior) / (n[c] + self.a) for c in tags] or [self.prior]
            out[i] = _clip(sum(ps) / len(ps))
            for c in tags:
                n[c] += 1
                k[c] += y
        return out


@dataclass
class BKTPredictor:
    """One BKT model per concept, with parameters fitted by EM (or fixed hand-set values)."""

    fit_params: bool = True
    combine: str = "conjunctive"  # how to turn per-concept mastery into one question's probability
    min_sequences: int = 20
    name: str = "BKT (fitted)"
    max_tags: int | None = None  # use only the first k tags of each question (None = all)
    # speed limits for datasets with hundreds of concepts
    max_fit_sequences: int | None = None
    max_fit_len: int | None = None
    n_random_starts: int = 2

    def _tags(self, tags: tuple) -> tuple:
        return tags if self.max_tags is None else tags[: self.max_tags]

    def fit(self, train: Iterable[Seq]) -> "BKTPredictor":
        per_concept: dict[str, list[np.ndarray]] = defaultdict(list)
        for seq in train:
            local: dict[str, list[int]] = defaultdict(list)
            for _, tags, y, _ in seq:
                for c in self._tags(tags):
                    local[c].append(y)
            for c, ys in local.items():
                if len(ys) >= 2:
                    per_concept[c].append(np.array(ys, dtype=np.int8))
        self.params: dict[str, BKTParams] = {}
        if self.fit_params:
            for c, seqs in per_concept.items():
                if len(seqs) >= self.min_sequences:
                    if self.max_fit_sequences and len(seqs) > self.max_fit_sequences:
                        seqs = seqs[: self.max_fit_sequences]
                    self.params[c] = bkt.fit_params(seqs, n_random=self.n_random_starts, max_len=self.max_fit_len)
        return self

    def params_for(self, c: str) -> BKTParams:
        return self.params.get(c, bkt.HAND_SET)

    def predict(self, seq: Seq) -> np.ndarray:
        state: dict[str, float] = {}
        out = np.empty(len(seq))
        for i, (_, tags, y, unsure) in enumerate(seq):
            tags = self._tags(tags)
            ps = [state.get(c, self.params_for(c).p_init) for c in tags]
            pr = [self.params_for(c) for c in tags]
            if not tags:
                out[i] = 0.5
                continue
            if self.combine == "conjunctive":
                # Every tagged concept must be mastered to answer without guessing.
                p_all = float(np.prod(ps))
                slip = sum(p.p_slip for p in pr) / len(pr)
                guess = sum(p.p_guess for p in pr) / len(pr)
                out[i] = _clip(p_all * (1 - slip) + (1 - p_all) * guess)
            else:  # "mean": average the per-concept predictions
                out[i] = _clip(sum(bkt.predict_correct(p, q) for p, q in zip(ps, pr)) / len(tags))
            for c, p in zip(tags, ps):
                state[c] = bkt.update(p, bool(y), self.params_for(c), unsure)
        return out


def evaluate(predictor, test: Iterable[Seq], skip_first: int = 0) -> dict[str, float]:
    """AUC, accuracy, log loss and RMSE over all answers in `test`.

    `skip_first` leaves out each learner's first few answers (no history to learn from yet).
    """
    from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

    ys: list[np.ndarray] = []
    ps: list[np.ndarray] = []
    for seq in test:
        if len(seq) <= skip_first:
            continue
        p = predictor.predict(seq)
        ys.append(np.array([s[2] for s in seq])[skip_first:])
        ps.append(p[skip_first:])
    y = np.concatenate(ys)
    p = np.concatenate(ps)
    return {
        "n": int(len(y)),
        "auc": float(roc_auc_score(y, p)) if len(set(y.tolist())) > 1 else float("nan"),
        "accuracy": float(accuracy_score(y, p >= 0.5)),
        "log_loss": float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6))),
        "rmse": float(np.sqrt(np.mean((y - p) ** 2))),
    }


def standard_ladder() -> list[Callable[[], object]]:
    return [
        GlobalMean,
        ItemMean,
        RunningAccuracy,
        lambda: BKTPredictor(fit_params=False, name="BKT (hand-set parameters)"),
        lambda: BKTPredictor(fit_params=True, name="BKT (fitted)"),
    ]
