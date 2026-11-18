"""The Python concept graph must match the one the frontend shows."""

import re
from pathlib import Path

import pytest

from circuit_coach.curriculum import CONCEPTS, CONTENT, MODULES

FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "src" / "data"
pytestmark = pytest.mark.skipif(not FRONTEND.exists(), reason="frontend sources not present")


def test_prerequisites_match_curriculum_ts():
    text = (FRONTEND / "curriculum.ts").read_text(encoding="utf8")
    for cid, d in CONCEPTS.items():
        m = re.search(rf'\b{cid}: \{{\s*id: "{cid}",.*?prereqs: \[([^\]]*)\]', text, re.S)
        assert m, cid
        ts = re.findall(r'"(\w+)"', m.group(1))
        assert ts == d["prereqs"], f"{cid}: frontend {ts} vs backend {d['prereqs']}"


def test_lesson_ids_match_content_ts():
    text = (FRONTEND / "content.ts").read_text(encoding="utf8")
    ts: dict[str, list[str]] = {}
    for m in re.finditer(r'id: "(ct_\w+)",\s*concept: "(\w+)"', text):
        ts.setdefault(m.group(2), []).append(m.group(1))
    assert ts == CONTENT


def test_columns_match_curriculum_ts():
    text = (FRONTEND / "curriculum.ts").read_text(encoding="utf8")
    for cid, d in CONCEPTS.items():
        m = re.search(rf'\b{cid}: \{{\s*id: "{cid}",.*?pos: \{{ col: (\d+)', text, re.S)
        assert m, cid
        assert int(m.group(1)) == d["col"], f"{cid}: frontend column {m.group(1)} vs backend {d['col']}"


def test_modules_match_curriculum_ts():
    text = (FRONTEND / "curriculum.ts").read_text(encoding="utf8")
    for mid, m in MODULES.items():
        found = re.search(rf'id: "{mid}",.*?concepts: \[([^\]]*)\]', text, re.S)
        assert found, mid
        assert re.findall(r'"(\w+)"', found.group(1)) == m["concepts"], mid


# ---- the browser engine's copies of the service's data files ---------------------------------


def test_browser_engine_carries_the_same_fitted_parameters():
    engine_dir = Path(__file__).resolve().parents[1] / "circuit_coach"
    assert (FRONTEND / "fittedParams.json").read_text(encoding="utf8") == (engine_dir / "fitted_params.json").read_text(encoding="utf8")


def test_browser_engine_carries_the_same_difficulty_table():
    engine_dir = Path(__file__).resolve().parents[1] / "circuit_coach"
    assert (FRONTEND / "itemDifficulty.json").read_text(encoding="utf8") == (engine_dir / "item_difficulty.json").read_text(encoding="utf8")


def _close(a, b, path="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return [f"{path}: keys differ"]
        return [d for k in a for d in _close(a[k], b[k], f"{path}/{k}")]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length differs"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in _close(x, y, f"{path}[{i}]")]
    if isinstance(a, float) and isinstance(b, float):
        return [] if abs(a - b) < 1e-9 else [f"{path}: {a} vs {b}"]
    return [] if a == b else [f"{path}: {a!r} vs {b!r}"]


def test_recorded_journeys_for_the_browser_engine_are_current():
    """`parity_cases.json` is what the service answers today; the browser engine is tested against it.

    If this fails, the service's behaviour changed: run `python scripts/export_parity_cases.py`
    and make the browser engine (`frontend/src/engine/engine.ts`) follow, until
    `npm test` passes again.
    """
    import json
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from export_parity_cases import OUT, build

    committed = json.loads(OUT.read_text(encoding="utf8"))
    problems = _close(json.loads(json.dumps(build())), committed)
    assert not problems, problems[:5]
