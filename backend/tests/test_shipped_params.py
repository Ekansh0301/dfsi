"""The parameters the service ships with are the frozen model (tag v0.9) and must not drift.

Evaluation scripts write their fits to results/ and touch circuit_coach/fitted_params.json only
with --write-service-params. If you change the file on purpose, update FROZEN_SHA256 below.
"""

import hashlib
import json
from pathlib import Path

from circuit_coach.curriculum import CONCEPTS
from circuit_coach.engine import load_params

PARAMS = Path(__file__).resolve().parents[1] / "circuit_coach" / "fitted_params.json"
FROZEN_SHA256 = "98af305df972cb4169ec5eb3b04be502c9a5795196acfdff2bbb32f6af82ddfe"


def raw() -> dict:
    return json.loads(PARAMS.read_text(encoding="utf8"))


def test_shipped_file_has_both_models_for_every_concept():
    d = raw()
    for section in ("concepts", "concepts_first_tag"):
        assert set(d[section]) == set(CONCEPTS), section
        for c, p in d[section].items():
            assert set(p) == {"p_init", "p_learn", "p_slip", "p_guess"}, (section, c)
            assert all(0 < v < 1 for v in p.values()), (section, c)


def test_improved_model_reads_its_own_first_tag_parameters():
    base, improved = load_params(model="baseline"), load_params(model="improved")
    first_tag = raw()["concepts_first_tag"]
    assert all(improved[c].as_dict() == first_tag[c] for c in CONCEPTS)
    assert any(base[c] != improved[c] for c in CONCEPTS)


def test_shipped_parameters_match_the_frozen_model():
    digest = hashlib.sha256(PARAMS.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert digest == FROZEN_SHA256, "fitted_params.json changed; rerun scripts without --write-service-params"
