import numpy as np

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
