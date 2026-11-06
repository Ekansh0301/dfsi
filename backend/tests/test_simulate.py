from circuit_coach.diagnosis_eval import true_blockers
from circuit_coach.simulate import simulate


def test_simulation_is_reproducible():
    a, _ = simulate(30, seed=3)
    b, _ = simulate(30, seed=3)
    assert [(r.item_id, r.correct) for r in a[0].responses] == [(r.item_id, r.correct) for r in b[0].responses]


def test_every_learner_has_responses_and_at_least_one_assessment():
    learners, _ = simulate(50, seed=1)
    assert all(l.responses and l.assess_points for l in learners)
    ap = learners[0].assess_points[0]
    assert ap.n_responses <= len(learners[0].responses) and set(ap.truth) >= set(ap.assessed)


def test_true_blocker_is_the_unmastered_concept_whose_prerequisites_are_mastered():
    truth = {c: True for c in ["safety", "quantities", "ohm", "symbols", "wiring", "multimeter", "series_parallel", "diagrams", "earthing", "fault"]}
    truth["symbols"] = False
    truth["diagrams"] = False
    assert true_blockers(truth, "diagrams") == {"symbols"}
    assert true_blockers(truth, "symbols") == {"symbols"}
    assert true_blockers(truth, "wiring") == set()


# ---- Barabari's quiz format in the simulator (PLAN S3-1) -----------------------------------

import collections
import hashlib
import tempfile
from pathlib import Path

from circuit_coach import dataset
from circuit_coach.simulate import SimConfig


def test_sprint2_config_reproduces_the_sprint2_simulator_exactly():
    """Learners and hidden truth hash to the files committed before Sprint 3."""
    with tempfile.TemporaryDirectory() as d:
        m = dataset.save(dataset.generate(500, 0, "sprint2"), Path(d))
    assert m["sha256"]["learners.csv"] == "62cbe2218bf429e72e73782bc387436b4b86e670b5af5e5f2fc1ee8509dcb2ea"
    assert m["sha256"]["ground_truth.csv"] == "9bdd698878aed8abd2c8d731537c5d36aa9e5924f7d08a1e843efa44aa6300b3"


def test_default_simulate_is_still_sprint2():
    a, _ = simulate(20, seed=2)
    b, _ = simulate(20, seed=2, config=SimConfig.sprint2())
    assert [(r.item_id, r.correct) for r in a[3].responses] == [(r.item_id, r.correct) for r in b[3].responses]
    assert all(r.question_type == "multiple_choice" and r.attempt == 1 for lr in a for r in lr.responses)


def test_barabari_items_have_types_points_and_difficulty():
    _, bank = simulate(1, seed=0, config=SimConfig())
    items = [i for b in bank.values() for i in b]
    kinds = collections.Counter(i.question_type for i in items)
    assert set(kinds) == {"multiple_choice", "true_false", "short_answer"}
    assert all(i.guess == 0.5 for i in items if i.question_type == "true_false")
    assert {i.points for i in items} <= {10.0, 20.0}
    assert len({round(i.difficulty, 3) for i in items}) > 100


def test_failed_quick_checks_are_retaken_and_attempts_count_up():
    learners, _ = simulate(300, seed=1, config=SimConfig())
    attempts = [r.attempt for lr in learners for r in lr.responses]
    assert max(attempts) == SimConfig().max_attempts and min(attempts) == 1
    for lr in learners[:50]:
        for module in {r.module for r in lr.responses}:
            seq = [r.attempt for r in lr.responses if r.module == module]
            assert seq[0] == 1 and all(b - a in (0, 1) or b == 1 for a, b in zip(seq, seq[1:]))


def test_no_retakes_when_switched_off():
    learners, _ = simulate(100, seed=1, config=SimConfig().with_(max_attempts=1))
    assert {r.attempt for lr in learners for r in lr.responses} == {1}


def test_short_answers_carry_a_score_in_quarters():
    learners, _ = simulate(200, seed=3, config=SimConfig())
    scores = [r.score for lr in learners for r in lr.responses if r.question_type == "short_answer"]
    assert scores and set(scores) <= {0.0, 0.25, 0.5, 0.75, 1.0}


def test_after_the_reveal_unknown_concepts_are_answered_from_memory_more_often():
    learners, _ = simulate(1500, seed=5, config=SimConfig())
    by_attempt = collections.defaultdict(list)
    for lr in learners:
        for r in lr.responses:
            if r.question_type != "short_answer":
                by_attempt[r.attempt].append(r.correct)
    rate = {k: sum(v) / len(v) for k, v in by_attempt.items()}
    assert rate[4] > rate[1]


def test_barabari_simulation_is_reproducible():
    a = dataset.generate(60, 9, "barabari")
    b = dataset.generate(60, 9, "barabari")
    key = lambda ds: [(r.item_id, r.correct, r.score, r.attempt) for lr in ds.learners for r in lr.responses]  # noqa: E731
    assert key(a) == key(b)
