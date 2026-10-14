import numpy as np
import pytest

from circuit_coach import bkt
from circuit_coach.bkt import BKTParams


def test_correct_answer_raises_mastery_and_wrong_lowers_it():
    p = 0.4
    params = bkt.HAND_SET
    assert bkt.update(p, True, params) > p
    assert bkt.update(p, False, params) < bkt.update(p, True, params)


def test_unsure_is_weaker_evidence_of_mastery_than_a_plain_wrong_answer():
    p = 0.5
    assert bkt.update(p, False, bkt.HAND_SET, unsure=True) < bkt.update(p, False, bkt.HAND_SET, unsure=False)


def test_mastery_stays_inside_bounds():
    p = 0.5
    for _ in range(200):
        p = bkt.update(p, True, bkt.HAND_SET)
    assert p <= bkt.P_MAX
    for _ in range(200):
        p = bkt.update(p, False, bkt.HAND_SET)
    assert p >= bkt.P_MIN


def test_learn_step_only_moves_up():
    assert bkt.learn_step(0.3, bkt.HAND_SET) > 0.3


def test_em_recovers_known_parameters():
    rng = np.random.default_rng(1)
    true = BKTParams(0.3, 0.15, 0.08, 0.22)
    seqs = []
    for _ in range(3000):
        mastered = rng.random() < true.p_init
        s = []
        for _ in range(int(rng.integers(4, 12))):
            s.append(int(rng.random() < (1 - true.p_slip if mastered else true.p_guess)))
            if not mastered and rng.random() < true.p_learn:
                mastered = True
        seqs.append(np.array(s))
    fit = bkt.fit_params(seqs)
    for name in ("p_init", "p_learn", "p_slip", "p_guess"):
        assert abs(getattr(fit, name) - getattr(true, name)) < 0.05, name


def test_fit_falls_back_to_hand_set_when_there_is_too_little_data():
    assert bkt.fit_params([np.array([1, 0, 1])]) == bkt.HAND_SET


# ---- exact update rules ---------------------------------------------------------------

P = BKTParams(p_init=0.3, p_learn=0.1, p_slip=0.1, p_guess=0.2)


def test_correct_answer_follows_the_bkt_formula():
    # posterior = 0.4 * 0.9 / (0.4 * 0.9 + 0.6 * 0.2) = 0.75, then learning: 0.75 + 0.25 * 0.1
    assert bkt.posterior(0.4, True, P) == pytest.approx(0.75)
    assert bkt.update(0.4, True, P) == pytest.approx(0.775)


def test_wrong_answer_follows_the_bkt_formula():
    # posterior = 0.4 * 0.1 / (0.4 * 0.1 + 0.6 * 0.8) = 0.04 / 0.52, then learning
    post = 0.04 / 0.52
    assert bkt.posterior(0.4, False, P) == pytest.approx(post)
    assert bkt.update(0.4, False, P) == pytest.approx(post + (1 - post) * 0.1)


def test_unsure_uses_a_near_zero_guess_rate():
    post = 0.4 * 0.1 / (0.4 * 0.1 + 0.6 * (1 - bkt.UNSURE_GUESS))
    assert bkt.posterior(0.4, False, P, unsure=True) == pytest.approx(post)


def test_more_guessing_makes_a_correct_answer_weaker_evidence():
    low, high = bkt.with_params(P, p_guess=0.1), bkt.with_params(P, p_guess=0.3)
    assert bkt.update(0.4, True, low) > bkt.update(0.4, True, high)


def test_more_slipping_makes_a_wrong_answer_weaker_evidence():
    low, high = bkt.with_params(P, p_slip=0.05), bkt.with_params(P, p_slip=0.25)
    assert bkt.update(0.4, False, low) < bkt.update(0.4, False, high)


def test_no_learning_means_the_update_is_just_the_posterior():
    still = bkt.with_params(P, p_learn=0.0)
    assert bkt.update(0.4, True, still) == pytest.approx(bkt.posterior(0.4, True, still))


def test_learn_step_follows_the_transition():
    assert bkt.learn_step(0.4, P) == pytest.approx(0.4 + 0.6 * 0.1)


def test_predicted_correctness_mixes_slip_and_guess():
    assert bkt.predict_correct(0.0, P) == pytest.approx(P.p_guess)
    assert bkt.predict_correct(1.0, P) == pytest.approx(1 - P.p_slip)
    assert bkt.predict_correct(0.5, P) == pytest.approx(0.5 * 0.9 + 0.5 * 0.2)


def test_params_round_trip_through_a_dict():
    assert BKTParams.from_dict(P.as_dict()) == P


# ---- multi-concept questions --------------------------------------------------------


def test_multi_concept_question_updates_each_concept_with_its_own_parameters():
    from circuit_coach.curriculum import CONCEPTS
    from circuit_coach.engine import Engine, Event, LearnerState

    params = {c: bkt.HAND_SET for c in CONCEPTS}
    params["wiring"] = bkt.with_params(bkt.HAND_SET, p_guess=0.3)
    e = Engine(params)
    start = LearnerState(mastery={"symbols": 0.4, "wiring": 0.4})
    out = e.trace(start, [Event(("symbols", "wiring"), True)])
    assert out.mastery["symbols"] == pytest.approx(bkt.update(0.4, True, params["symbols"]))
    assert out.mastery["wiring"] == pytest.approx(bkt.update(0.4, True, params["wiring"]))
    assert out.observations == {"symbols": 1, "wiring": 1}
    assert start.mastery == {"symbols": 0.4, "wiring": 0.4}, "tracing must not change the input state"


def test_unknown_concept_tags_are_ignored_by_the_tracer():
    from circuit_coach.curriculum import CONCEPTS
    from circuit_coach.engine import Engine, Event, LearnerState

    e = Engine({c: bkt.HAND_SET for c in CONCEPTS})
    out = e.trace(LearnerState(), [Event(("symbols", "not_a_concept"), True)])
    assert set(out.observations) == {"symbols"}


# ---- parameter recovery with EM -----------------------------------------------------


def simulate_bkt(true: BKTParams, n: int, seed: int) -> list[np.ndarray]:
    """Learners who follow the BKT model exactly."""
    rng = np.random.default_rng(seed)
    seqs = []
    for _ in range(n):
        mastered = rng.random() < true.p_init
        s = []
        for _ in range(int(rng.integers(4, 12))):
            s.append(int(rng.random() < (1 - true.p_slip if mastered else true.p_guess)))
            if not mastered and rng.random() < true.p_learn:
                mastered = True
        seqs.append(np.array(s))
    return seqs


@pytest.mark.parametrize(
    "true",
    [
        BKTParams(0.2, 0.10, 0.05, 0.15),
        BKTParams(0.5, 0.20, 0.12, 0.25),
        BKTParams(0.1, 0.25, 0.08, 0.30),
    ],
    ids=["low-start", "half-known", "fast-learner-high-guess"],
)
def test_em_recovers_several_known_parameter_sets(true):
    fit = bkt.fit_params(simulate_bkt(true, 3000, seed=7))
    for name in ("p_init", "p_learn", "p_slip", "p_guess"):
        assert abs(getattr(fit, name) - getattr(true, name)) < 0.05, (name, getattr(fit, name))


def test_em_fit_beats_the_hand_set_parameters_on_likelihood():
    seqs = simulate_bkt(BKTParams(0.5, 0.2, 0.12, 0.25), 1000, seed=3)
    obs, mask = bkt._pad(seqs)
    fit = bkt.fit_params(seqs)
    _, ll_fit = bkt._em_once(obs, mask, fit, iters=1, tol=0)
    _, ll_hand = bkt._em_once(obs, mask, bkt.HAND_SET, iters=1, tol=0)
    assert ll_fit > ll_hand


def test_fitted_parameters_stay_inside_the_bounds():
    # All answers right: EM would push slip to 0 and guess to 1 without bounds.
    fit = bkt.fit_params([np.ones(8, dtype=np.int8) for _ in range(50)])
    for name, (lo, hi) in bkt.BOUNDS.items():
        assert lo <= getattr(fit, name) <= hi, name


def test_fitting_is_reproducible():
    seqs = simulate_bkt(BKTParams(0.3, 0.15, 0.08, 0.22), 500, seed=5)
    assert bkt.fit_params(seqs, seed=1) == bkt.fit_params(seqs, seed=1)
