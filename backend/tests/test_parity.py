"""The Python concept graph must match the one the frontend shows."""

import re
from pathlib import Path

import pytest

from circuit_coach.curriculum import CONCEPTS, CONTENT

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
