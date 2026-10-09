"""Standard Bayesian Knowledge Tracing (BKT), one independent model per concept.

Each concept is a two-state hidden Markov model: the learner has either "not mastered" or
"mastered" it. Four parameters describe it:

    p_init   probability the concept is already mastered before the first question
    p_learn  probability of moving from not mastered to mastered after each opportunity
    p_slip   probability of a wrong answer while mastered
    p_guess  probability of a right answer while not mastered

There is no forgetting (mastered stays mastered) and no knowledge of prerequisites. That
independence is the known weakness of this baseline. It is what the prerequisite-aware model
planned for Sprint 3 is meant to fix.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

P_MIN, P_MAX = 0.01, 0.99
# "I'm not sure" is evidence of not knowing the concept without the chance of a lucky guess.
UNSURE_GUESS = 0.02


@dataclass(frozen=True)
class BKTParams:
    p_init: float = 0.25
    p_learn: float = 0.12
    p_slip: float = 0.10
    p_guess: float = 0.20

    def as_dict(self) -> dict[str, float]:
        return {"p_init": self.p_init, "p_learn": self.p_learn, "p_slip": self.p_slip, "p_guess": self.p_guess}

    @staticmethod
    def from_dict(d: dict[str, float]) -> "BKTParams":
        return BKTParams(d["p_init"], d["p_learn"], d["p_slip"], d["p_guess"])


# Hand-set values used by the in-browser prototype. Kept as the unfitted reference point.
HAND_SET = BKTParams()


def _clamp(x: float) -> float:
    return min(P_MAX, max(P_MIN, x))


def posterior(p: float, correct: bool, params: BKTParams, unsure: bool = False) -> float:
    """P(mastered | this answer), before applying the learning step."""
    guess = min(params.p_guess, UNSURE_GUESS) if unsure else params.p_guess
    s = params.p_slip
    if correct:
        num = p * (1 - s)
        return num / (num + (1 - p) * guess)
    num = p * s
    return num / (num + (1 - p) * (1 - guess))


def update(p: float, correct: bool, params: BKTParams, unsure: bool = False) -> float:
    """One full BKT step: condition on the answer, then apply the learning transition."""
    post = posterior(p, correct, params, unsure)
    return _clamp(post + (1 - post) * params.p_learn)


def learn_step(p: float, params: BKTParams) -> float:
    """A lesson is a learning opportunity: apply the transition only."""
    return _clamp(p + (1 - p) * params.p_learn)


def predict_correct(p_mastered: float, params: BKTParams) -> float:
    return p_mastered * (1 - params.p_slip) + (1 - p_mastered) * params.p_guess


# --------------------------------------------------------------------------------------
# Fitting with expectation maximisation (Baum-Welch on the two-state model)
# --------------------------------------------------------------------------------------

# Bounds keep the model identifiable: a mastered learner is mostly right, and guessing is
# bounded so "not mastered" cannot absorb everything.
BOUNDS = {"p_init": (0.01, 0.99), "p_learn": (0.001, 0.6), "p_slip": (0.001, 0.30), "p_guess": (0.001, 0.35)}


def _pad(sequences: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    n = len(sequences)
    t = max(len(s) for s in sequences)
    obs = np.zeros((n, t), dtype=np.int8)
    mask = np.zeros((n, t), dtype=bool)
    for i, s in enumerate(sequences):
        obs[i, : len(s)] = s
        mask[i, : len(s)] = True
    return obs, mask


def _em_once(obs: np.ndarray, mask: np.ndarray, start: BKTParams, iters: int, tol: float) -> tuple[BKTParams, float]:
    n, t = obs.shape
    pi, pl, ps, pg = start.p_init, start.p_learn, start.p_slip, start.p_guess
    last_ll = -np.inf
    obs_f = obs.astype(float)
    for _ in range(iters):
        # emission likelihood of the observed answer in each state: columns = (not mastered, mastered)
        e0 = np.where(obs == 1, pg, 1 - pg)
        e1 = np.where(obs == 1, 1 - ps, ps)
        e0 = np.where(mask, e0, 1.0)
        e1 = np.where(mask, e1, 1.0)

        alpha = np.zeros((n, t, 2))
        scale = np.zeros((n, t))
        a0 = np.stack([np.full(n, 1 - pi) * e0[:, 0], np.full(n, pi) * e1[:, 0]], axis=1)
        scale[:, 0] = a0.sum(axis=1)
        alpha[:, 0] = a0 / scale[:, [0]]
        for k in range(1, t):
            prev = alpha[:, k - 1]
            p1 = prev[:, 1] + prev[:, 0] * pl  # mastered after the transition
            p0 = prev[:, 0] * (1 - pl)
            a = np.stack([p0 * e0[:, k], p1 * e1[:, k]], axis=1)
            s = a.sum(axis=1)
            scale[:, k] = s
            alpha[:, k] = a / s[:, None]
        # padded steps multiply the likelihood by 1 (scale of exactly the previous mass); drop them
        ll = float(np.log(scale, where=mask, out=np.zeros_like(scale)).sum())

        beta = np.ones((n, t, 2))
        for k in range(t - 2, -1, -1):
            nxt = beta[:, k + 1]
            m = mask[:, k + 1]
            b0 = (1 - pl) * e0[:, k + 1] * nxt[:, 0] + pl * e1[:, k + 1] * nxt[:, 1]
            b1 = e1[:, k + 1] * nxt[:, 1]
            b = np.stack([b0, b1], axis=1) / scale[:, [k + 1]]
            beta[:, k] = np.where(m[:, None], b, 1.0)

        gamma = alpha * beta
        gamma /= gamma.sum(axis=2, keepdims=True)

        # transition expectation: P(not mastered at k, mastered at k+1 | all data)
        m_next = mask[:, 1:]
        xi01 = (
            alpha[:, :-1, 0] * pl * e1[:, 1:] * beta[:, 1:, 1] / scale[:, 1:]
        )
        xi01 = np.where(m_next, xi01, 0.0)
        g0_prev = np.where(m_next, gamma[:, :-1, 0], 0.0)

        pi = float(gamma[:, 0, 1].mean())
        pl = float(xi01.sum() / max(g0_prev.sum(), 1e-9))
        g0 = np.where(mask, gamma[:, :, 0], 0.0)
        g1 = np.where(mask, gamma[:, :, 1], 0.0)
        pg = float((g0 * obs_f).sum() / max(g0.sum(), 1e-9))
        ps = float((g1 * (1 - obs_f)).sum() / max(g1.sum(), 1e-9))

        pi = float(np.clip(pi, *BOUNDS["p_init"]))
        pl = float(np.clip(pl, *BOUNDS["p_learn"]))
        ps = float(np.clip(ps, *BOUNDS["p_slip"]))
        pg = float(np.clip(pg, *BOUNDS["p_guess"]))

        if abs(ll - last_ll) < tol:
            break
        last_ll = ll
    return BKTParams(pi, pl, ps, pg), ll


def fit_params(
    sequences: list[np.ndarray], iters: int = 80, tol: float = 1e-3, seed: int = 0, n_random: int = 2, max_len: int | None = None
) -> BKTParams:
    """Fit one concept's four parameters from learners' correct/incorrect sequences.

    `sequences` holds one 0/1 array per learner, in the order the learner answered. Several
    starting points are tried and the best likelihood wins, because EM can stall in a
    poor local maximum.
    """
    sequences = [np.asarray(s, dtype=np.int8)[:max_len] for s in sequences if len(s) >= 2]
    if len(sequences) < 5:
        return HAND_SET
    obs, mask = _pad(sequences)
    rng = np.random.default_rng(seed)
    starts = [
        HAND_SET,
        BKTParams(0.5, 0.2, 0.1, 0.25),
        BKTParams(0.1, 0.05, 0.15, 0.15),
    ] + [
        BKTParams(
            float(rng.uniform(0.05, 0.7)),
            float(rng.uniform(0.02, 0.35)),
            float(rng.uniform(0.03, 0.2)),
            float(rng.uniform(0.05, 0.3)),
        )
        for _ in range(n_random)
    ]
    best, best_ll = HAND_SET, -np.inf
    for s in starts:
        params, ll = _em_once(obs, mask, s, iters, tol)
        if ll > best_ll:
            best, best_ll = params, ll
    return best


def with_params(params: BKTParams, **kw: float) -> BKTParams:
    return replace(params, **kw)
