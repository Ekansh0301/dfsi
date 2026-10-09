"""Concept graph, modules and lesson ids for the demo electrician track.

This mirrors `frontend/src/data/curriculum.ts` and `content.ts`. `tests/test_parity.py`
fails if the two drift apart.
"""

from __future__ import annotations

# concept id -> (English name, Hindi name, prerequisites, column in the concept map)
# A prerequisite edge A -> B means "A must be understood before B".
CONCEPTS: dict[str, dict] = {
    "safety": {"en": "Electrical safety", "hi": "बिजली से सुरक्षा", "prereqs": [], "col": 0},
    "quantities": {"en": "Voltage, current & resistance", "hi": "वोल्टेज, करंट और रेज़िस्टेंस", "prereqs": ["safety"], "col": 1},
    "ohm": {"en": "Ohm's law", "hi": "ओम का नियम", "prereqs": ["quantities"], "col": 2},
    "symbols": {"en": "Circuit symbols", "hi": "सर्किट के चिह्न", "prereqs": ["quantities"], "col": 2},
    "wiring": {"en": "Switch & lamp wiring", "hi": "स्विच और बल्ब की वायरिंग", "prereqs": ["safety", "quantities"], "col": 2},
    "multimeter": {"en": "Using a multimeter", "hi": "मल्टीमीटर का उपयोग", "prereqs": ["safety", "quantities"], "col": 2},
    "series_parallel": {"en": "Series & parallel circuits", "hi": "सीरीज़ और पैरेलल सर्किट", "prereqs": ["ohm"], "col": 3},
    "diagrams": {"en": "Reading circuit diagrams", "hi": "सर्किट डायग्राम", "prereqs": ["symbols", "wiring"], "col": 3},
    "earthing": {"en": "Earthing, MCB & fuse", "hi": "अर्थिंग, MCB और फ्यूज़", "prereqs": ["safety", "wiring"], "col": 3},
    "fault": {
        "en": "Fault finding",
        "hi": "फॉल्ट की पहचान",
        "prereqs": ["diagrams", "multimeter", "series_parallel"],
        "col": 4,
    },
}

CONCEPT_ORDER = list(CONCEPTS)

# module id -> (number, concepts assessed by its quick check)
MODULES: dict[str, dict] = {
    "m1": {"number": 1, "concepts": ["safety"]},
    "m2": {"number": 2, "concepts": ["quantities", "ohm"]},
    "m3": {"number": 3, "concepts": ["symbols", "wiring", "diagrams"]},
    "m4": {"number": 4, "concepts": ["series_parallel", "diagrams"]},
    "m5": {"number": 5, "concepts": ["multimeter"]},
    "m6": {"number": 6, "concepts": ["earthing", "fault"]},
}

# concept id -> lesson ids, in recommendation order (the first untried one is chosen)
CONTENT: dict[str, list[str]] = {
    "diagrams": ["ct_diag_walk", "ct_diag_practice", "ct_diag_example"],
    "symbols": ["ct_sym_cards", "ct_sym_practice"],
    "wiring": ["ct_wiring_walk", "ct_wiring_practice"],
    "series_parallel": ["ct_sp_walk", "ct_sp_example"],
    "safety": ["ct_safety_walk"],
    "quantities": ["ct_quant_walk"],
    "ohm": ["ct_ohm_walk"],
    "multimeter": ["ct_mm_walk"],
    "earthing": ["ct_earth_walk"],
    "fault": ["ct_fault_walk"],
}


def prereqs(concept: str) -> list[str]:
    return CONCEPTS[concept]["prereqs"]


def ancestors(concept: str) -> set[str]:
    """Every concept that must be understood (directly or not) before `concept`."""
    out: set[str] = set()
    stack = list(prereqs(concept))
    while stack:
        c = stack.pop()
        if c not in out:
            out.add(c)
            stack.extend(prereqs(c))
    return out


def topological_order() -> list[str]:
    """Concepts ordered so that prerequisites come first."""
    seen: list[str] = []

    def visit(c: str) -> None:
        if c in seen:
            return
        for p in prereqs(c):
            visit(p)
        seen.append(c)

    for c in CONCEPT_ORDER:
        visit(c)
    return seen
