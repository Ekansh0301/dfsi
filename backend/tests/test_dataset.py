from pathlib import Path

import pytest

from circuit_coach import dataset
from circuit_coach.curriculum import CONCEPT_ORDER

COMMITTED = Path(__file__).resolve().parents[1] / "datasets" / "synthetic_seed0"


@pytest.fixture(scope="module")
def ds():
    return dataset.generate(300, seed=4)


def test_split_is_70_30_by_learner(ds):
    assert len(ds.train) == 210 and len(ds.test) == 90
    assert {l.id for l in ds.train}.isdisjoint({l.id for l in ds.test})
    assert len(ds.train) + len(ds.test) == len(ds.learners)


def test_generation_and_split_are_reproducible():
    a, b = dataset.generate(60, seed=9), dataset.generate(60, seed=9)
    assert a.split == b.split
    assert [(r.item_id, r.correct, r.unsure) for r in a.learners[5].responses] == [(r.item_id, r.correct, r.unsure) for r in b.learners[5].responses]
    assert dataset.generate(60, seed=10).split != a.split


def test_a_generated_dataset_passes_validation(ds):
    assert dataset.validate(ds) == []


def test_ground_truth_is_kept_for_every_assessment_point(ds):
    for lr in ds.learners[:50]:
        assert lr.assess_points
        for ap in lr.assess_points:
            assert set(ap.truth) == set(CONCEPT_ORDER)


def test_saved_files_are_identical_for_the_same_seed(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    ma = dataset.save(dataset.generate(80, seed=2), a)
    mb = dataset.save(dataset.generate(80, seed=2), b)
    assert ma["sha256"] == mb["sha256"]
    assert dataset.verify_files(a) == []


def test_round_trip_through_files_keeps_everything(tmp_path):
    original = dataset.generate(80, seed=2)
    dataset.save(original, tmp_path)
    loaded = dataset.load(tmp_path)
    assert loaded.split == original.split and loaded.seed == 2
    assert dataset.validate(loaded) == []
    for x, y in zip(original.learners, loaded.learners):
        assert x.experience == y.experience and x.responses == y.responses and x.assess_points == y.assess_points


def test_editing_a_file_is_detected(tmp_path):
    dataset.save(dataset.generate(40, seed=1), tmp_path)
    p = tmp_path / "responses.csv"
    p.write_text(p.read_text(encoding="utf8").replace(",1,", ",0,", 1), encoding="utf8")
    assert dataset.verify_files(tmp_path) == ["responses.csv does not match its checksum"]


def test_validation_catches_broken_data():
    broken = dataset.generate(40, seed=1)
    broken.learners[0].responses[0].item_id = "no_such_item"
    broken.learners[1].responses[0].unsure, broken.learners[1].responses[0].correct = True, True
    broken.split[2] = "validation"
    problems = " ".join(dataset.validate(broken))
    assert "unknown item no_such_item" in problems
    assert "unsure answer marked correct" in problems
    assert "other than train and test" in problems


def test_the_committed_dataset_is_intact_and_valid():
    if not COMMITTED.exists():
        pytest.skip("run python scripts/generate_dataset.py")
    assert dataset.verify_files(COMMITTED) == []
    loaded = dataset.load(COMMITTED)
    assert dataset.validate(loaded) == []
    assert dataset.generate(len(loaded.learners), loaded.seed).split == loaded.split
