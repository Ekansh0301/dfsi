"""Write the API contract (OpenAPI schema) to docs/openapi.json.

    python scripts/export_openapi.py

Run this after changing a request or response model. `tests/test_contract.py` fails if the
committed file and the code disagree.
"""

from __future__ import annotations

import json
from pathlib import Path

from circuit_coach.api import app

OUT = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"


def render() -> str:
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    OUT.write_text(render(), encoding="utf8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
