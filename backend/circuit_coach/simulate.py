"""Made-up learners with known hidden mastery, for evaluating the engine.

Why synthetic data: real learner data from the NGOs does not exist yet, and real datasets do
not tell us which concept a learner "really" lacked. Here the hidden state is known, so we
can check whether the engine finds the right gap and the right root cause.

Generative story (kept deliberately simple and written down so its limits are clear):

* Each learner has a hidden mastered / not mastered flag for each of the 10 concepts.
* Starting mastery depends on experience and on prerequisites: a concept is rarely mastered
  while one of its prerequisites is not.
* Every response is a learning opportunity for the concepts it is tagged with, but learning
  is much slower while a prerequisite is unmastered. This is the structure that a plain
  per-concept BKT model cannot see.
* A question tagged with several concepts needs all of them: it is answered correctly with
  probability (1 - slip) if all are mastered, otherwise by guessing. Learners who do not know
  sometimes pick "I'm not sure" instead of guessing.
* Learners take the modules in order, with some dropping out, and practise concepts they
  got wrong.

`SimConfig` switches on the parts of Barabari's quiz format (PLAN S3-1): true/false and
short-answer questions, points per question, per-question difficulty, and retakes of a failed
quick check (pass mark 60%, answers revealed after 3 attempts, so a learner may then answer
from memory). `SimConfig.sprint2()` turns them all off and draws exactly the same random
numbers as the Sprint 2 simulator, so the earlier results stay reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from .curriculum import CONCEPT_ORDER, CONCEPTS, MODULES, prereqs, topological_order

QUIZ_LENGTH = {"m1": 3, "m2": 3, "m3": 5, "m4": 3, "m5": 3, "m6": 3}
EXPERIENCE = {"new": (0.30, 0.25), "some": (0.50, 0.55), "experienced": (0.20, 0.80)}  # (share, base mastery)
P_LEARN = 0.12
P_LESSON = 0.35
PREREQ_LEARN_FACTOR = 0.2  # learning speed while a prerequisite is unmastered
P_UNSURE_WHEN_UNKNOWN = 0.3
ITEMS_PER_CONCEPT = 14
P_MULTI_TAG = 0.3


@dataclass(frozen=True)
class SimConfig:
    """Which parts of Barabari's quiz format the made-up learners follow."""

    name: str = "barabari"
    p_true_false: float = 0.2  # share of items that are true/false questions
    p_short_answer: float = 0.1  # share of items that are instructor-marked short answers
    difficulty_sd: float = 0.8  # spread of per-question difficulty on the logit scale (0 = off)
    max_attempts: int = 4  # 1 = no retakes
    p_retake: float = 0.8  # chance a learner retakes a failed quick check
    pass_share: float = 0.6  # Barabari's default pass mark
    reveal_after: int = 3  # correct answers shown after this many attempts
    p_feedback_recall: float = 0.15  # right/wrong feedback helps a little on attempts 2 and 3
    p_reveal_recall: float = 0.6  # after the reveal, a learner may simply remember the answer

    @staticmethod
    def sprint2() -> "SimConfig":
        return SimConfig("sprint2", 0.0, 0.0, 0.0, 1, 0.0, 0.6, 3, 0.0, 0.0)

    @staticmethod
    def named(name: str) -> "SimConfig":
        return {"sprint2": SimConfig.sprint2(), "barabari": SimConfig()}[name]

    def with_(self, **kw) -> "SimConfig":
        return replace(self, **kw)


@dataclass(frozen=True)
class Item:
    id: str
    concepts: tuple[str, ...]
    slip: float
    guess: float
    question_type: str = "multiple_choice"
    points: float = 1.0
    difficulty: float = 0.0  # logit shift: positive = harder (more slips, fewer lucky guesses)


@dataclass
class Response:
    item_id: str
    concepts: tuple[str, ...]
    correct: bool
    unsure: bool
    module: str
    question_type: str = "multiple_choice"
    score: float | None = None  # partial credit for a short answer
    attempt: int = 1
    points: float = 1.0


@dataclass
class AssessPoint:
    """The moment a module quick check ends: what the engine has seen, and the hidden truth."""

    module: str
    n_responses: int  # responses observed so far (the prefix of `responses`)
    assessed: list[str]
    truth: dict[str, bool]  # concept -> truly mastered at this moment


@dataclass
class SimLearner:
    id: int
    experience: str
    responses: list[Response] = field(default_factory=list)
    assess_points: list[AssessPoint] = field(default_factory=list)


def _logit(x: float) -> float:
    return float(np.log(x / (1 - x)))


def _sigmoid(x: float) -> float:
    return float(1 / (1 + np.exp(-x)))


def make_item_bank(rng: np.random.Generator, config: SimConfig | None = None) -> dict[str, list[Item]]:
    config = config or SimConfig.sprint2()
    bank: dict[str, list[Item]] = {}
    for c in CONCEPT_ORDER:
        items = []
        for k in range(ITEMS_PER_CONCEPT):
            tags = (c,)
            if rng.random() < P_MULTI_TAG:
                pool = prereqs(c) or [x for x in CONCEPT_ORDER if x != c and CONCEPTS[x]["col"] <= CONCEPTS[c]["col"]]
                if pool:
                    tags = (c, str(rng.choice(pool)))
            slip, guess = float(rng.uniform(0.04, 0.14)), float(rng.uniform(0.15, 0.30))
            item = Item(f"s_{c}_{k}", tags, slip, guess)
            if config.name != "sprint2":  # extra draws only here, so Sprint 2 runs stay identical
                u = float(rng.random())
                qtype = "true_false" if u < config.p_true_false else "short_answer" if u < config.p_true_false + config.p_short_answer else "multiple_choice"
                d = float(rng.normal(0.0, config.difficulty_sd)) if config.difficulty_sd > 0 else 0.0
                slip = _sigmoid(_logit(slip) + d)
                guess = {"true_false": 0.5, "short_answer": 0.05}.get(qtype, _sigmoid(_logit(guess) - d))
                item = Item(item.id, tags, slip, guess, qtype, 20.0 if d > 0.5 else 10.0, d)
            items.append(item)
        bank[c] = items
    return bank


def _prereqs_ok(mastered: dict[str, bool], c: str) -> bool:
    return all(mastered[p] for p in prereqs(c))


def _learn(mastered: dict[str, bool], c: str, p: float, rng: np.random.Generator) -> None:
    if mastered[c]:
        return
    if not _prereqs_ok(mastered, c):
        p *= PREREQ_LEARN_FACTOR
    if rng.random() < min(p, 0.9):
        mastered[c] = True


def simulate_learner(lid: int, bank: dict[str, list[Item]], rng: np.random.Generator, config: SimConfig | None = None) -> SimLearner:
    config = config or SimConfig.sprint2()
    kinds = list(EXPERIENCE)
    experience = str(rng.choice(kinds, p=[EXPERIENCE[k][0] for k in kinds]))
    base = EXPERIENCE[experience][1]
    speed = float(np.exp(rng.normal(0.0, 0.35)))

    mastered: dict[str, bool] = {}
    for c in topological_order():
        if not prereqs(c):
            mastered[c] = bool(rng.random() < base)
        elif _prereqs_ok(mastered, c):
            mastered[c] = bool(rng.random() < base * 0.7)
        else:
            mastered[c] = bool(rng.random() < 0.03)

    learner = SimLearner(lid, experience)
    seen: set[str] = set()

    def recall(attempt: int) -> float:
        if attempt <= 1:
            return 0.0
        return config.p_reveal_recall if attempt > config.reveal_after else config.p_feedback_recall

    def ask(item: Item, module: str, attempt: int = 1) -> float:
        """Answer one item; returns the share of its points earned."""
        knows = all(mastered[c] for c in item.concepts)
        unsure, score = False, None
        if item.question_type == "short_answer":
            mean = 0.85 if knows else 0.2
            score = round(min(1.0, max(0.0, float(rng.normal(mean, 0.15)))) * 4) / 4  # marked in quarters
            correct = score >= 0.5
        elif knows:
            correct = bool(rng.random() < 1 - item.slip)
        elif attempt > 1 and rng.random() < recall(attempt):
            correct = True  # remembered from feedback or the revealed answer, not mastery
        elif rng.random() < P_UNSURE_WHEN_UNKNOWN:
            correct, unsure = False, True
        else:
            correct = bool(rng.random() < item.guess)
        learner.responses.append(Response(item.id, item.concepts, correct, unsure, module, item.question_type, score, attempt, item.points))
        seen.add(item.id)
        for c in item.concepts:
            _learn(mastered, c, P_LEARN * speed, rng)
        return score if score is not None else float(correct)

    def pick(concepts: list[str], k: int) -> list[Item]:
        out: list[Item] = []
        # one question on each assessed concept first, then fill up at random
        for c in concepts[:k]:
            fresh = [i for i in bank[c] if i.id not in seen] or bank[c]
            out.append(fresh[int(rng.integers(len(fresh)))])
        while len(out) < k:
            c = concepts[int(rng.integers(len(concepts)))]
            fresh = [i for i in bank[c] if i.id not in seen and i not in out] or bank[c]
            out.append(fresh[int(rng.integers(len(fresh)))])
        return out

    for mid, m in MODULES.items():
        quiz = pick(m["concepts"], QUIZ_LENGTH[mid])
        total = sum(i.points for i in quiz)
        for attempt in range(1, config.max_attempts + 1):
            got_wrong: set[str] = set()
            earned = 0.0
            for item in quiz:
                got = ask(item, mid, attempt)
                earned += got * item.points
                if got < 0.5:
                    got_wrong.update(item.concepts)
            if earned / total >= config.pass_share or attempt == config.max_attempts:
                break
            if rng.random() > config.p_retake:
                break
        learner.assess_points.append(
            AssessPoint(mid, len(learner.responses), list(m["concepts"]), dict(mastered))
        )
        # Practise what was got wrong: a lesson, then two more questions on the concept.
        for c in sorted(got_wrong & set(m["concepts"])):
            _learn(mastered, c, P_LESSON * speed, rng)
            for item in pick([c], 2):
                ask(item, mid)
        if rng.random() > 0.9:  # some learners drop out
            break
    return learner


def simulate(n_learners: int, seed: int = 0, config: SimConfig | None = None) -> tuple[list[SimLearner], dict[str, list[Item]]]:
    """Made-up learners. Without `config` this is the Sprint 2 simulator, unchanged."""
    config = config or SimConfig.sprint2()
    rng = np.random.default_rng(seed)
    bank = make_item_bank(rng, config)
    return [simulate_learner(i, bank, rng, config) for i in range(n_learners)], bank


def concept_sequences(learners: list[SimLearner], concept: str) -> list[np.ndarray]:
    """Correct/incorrect sequences for one concept, one per learner, in answer order.

    A response tagged with several concepts appears in each of their sequences (the naive
    credit assignment the baseline BKT uses).
    """
    out = []
    for lr in learners:
        seq = [int(r.correct) for r in lr.responses if concept in r.concepts]
        if len(seq) >= 2:
            out.append(np.array(seq, dtype=np.int8))
    return out
