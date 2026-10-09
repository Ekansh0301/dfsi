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
