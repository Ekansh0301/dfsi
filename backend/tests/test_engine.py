from circuit_coach.bkt import HAND_SET
from circuit_coach.curriculum import CONCEPTS
from circuit_coach.engine import Engine, Event, LearnerState


def engine(prereqs=True) -> Engine:
    return Engine({c: HAND_SET for c in CONCEPTS}, use_prerequisites=prereqs)


def ev(tags, ok, unsure=False):
    return Event(tuple(tags), ok, unsure)


def placement_good():
    """Onboarded learner who did well on the basics (mirrors the prototype's scenario)."""
    e = engine()
    state, start = e.onboard("some", [ev([c], True) for c in ("safety", "quantities", "ohm", "symbols", "wiring", "multimeter")])
    return e, state, start


def test_onboarding_skips_ahead_when_basics_are_known():
    _, _, start = placement_good()
    assert start in {"m3", "m4"}


def test_direct_gap_names_the_assessed_concept():
    e, state, _ = placement_good()
    state = e.trace(state, [ev(["symbols"], True), ev(["wiring"], True), ev(["diagrams"], False), ev(["diagrams"], False)])
    rec = e.recommend(state, ["symbols", "wiring", "diagrams"])
    assert rec["concept_id"] == "diagrams" and rec["chain"] == ["diagrams"]
    assert rec["recommended_content_id"] == "ct_diag_walk"


def test_root_cause_walks_back_to_a_weak_prerequisite():
    e, state, _ = placement_good()
    state = e.trace(state, [ev(["symbols"], False), ev(["symbols"], False), ev(["wiring"], True), ev(["diagrams"], False)])
    rec = e.recommend(state, ["symbols", "wiring", "diagrams"])
    assert rec["observed_concept_id"] == "diagrams"
    assert rec["concept_id"] == "symbols"
    assert rec["chain"] == ["diagrams", "symbols"]


def test_without_the_prerequisite_walk_the_assessed_concept_is_recommended():
    e = engine(prereqs=False)
    state, _ = e.onboard("some", [ev(["symbols"], False), ev(["symbols"], False)])
    state = e.trace(state, [ev(["diagrams"], False)])
    assert e.recommend(state, ["symbols", "diagrams"])["concept_id"] == "diagrams"


def test_unobserved_prerequisites_are_not_blamed():
    e = engine()
    state = e.trace(LearnerState(), [ev(["diagrams"], False), ev(["diagrams"], False)])
    assert e.recommend(state, ["diagrams"])["concept_id"] == "diagrams"


def test_no_recommendation_when_everything_is_strong():
    e = engine()
    state = e.trace(LearnerState(), [ev(["safety"], True)] * 5)
    assert e.recommend(state, ["safety"]) is None


def test_lessons_already_tried_are_skipped():
    e = engine()
    state = e.trace(LearnerState(), [ev(["diagrams"], False)] * 3)
    state.tried = {"diagrams": ["ct_diag_walk"]}
    assert e.recommend(state, ["diagrams"])["recommended_content_id"] == "ct_diag_practice"


def test_repeat_gap_uses_a_new_lesson_and_is_flagged():
    e = engine()
    state = e.trace(LearnerState(), [ev(["diagrams"], False)] * 3)
    state.tried = {"diagrams": ["ct_diag_walk"]}
    rec = e.recommend_repeat(state, "diagrams")
    assert rec["repeat_gap"] is True and rec["recommended_content_id"] != "ct_diag_walk"


def test_got_it_raises_mastery_but_not_to_certainty():
    e = engine()
    state = e.trace(LearnerState(), [ev(["diagrams"], False)] * 2)
    before = state.mastery["diagrams"]
    after = e.got_it(state, "diagrams").mastery["diagrams"]
    assert before < after < 0.6


def test_multi_concept_question_updates_every_tag():
    e = engine()
    state = e.trace(LearnerState(), [ev(["symbols", "wiring"], False)])
    assert state.observations == {"symbols": 1, "wiring": 1}
