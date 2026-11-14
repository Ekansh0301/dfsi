"""The paired, run-by-run comparison of the two models (scripts/paired_comparison.py)."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("paired_comparison", ROOT / "scripts" / "paired_comparison.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


def results():
    runs = json.loads((ROOT / "results" / "model_comparison.json").read_text(encoding="utf8"))
    return {sim: pc.paired(runs[sim]) for sim in ("sprint2", "barabari")}


def test_every_measure_is_compared_on_both_simulators():
    r = results()
    assert [len(r[s]) for s in ("sprint2", "barabari")] == [7, 7]
    assert all(row["runs"] == 5 for s in r for row in r[s])


def test_missed_gaps_on_the_sprint2_simulator_are_worse_in_most_runs():
    row = next(x for x in results()["sprint2"] if x["measure"] == "Missed gaps")
    assert row["better_runs"] == 1 and row["median_diff"] > 0
    assert row["verdict"] == "no clear difference"


def test_a_difference_is_called_only_when_the_interval_excludes_zero():
    for rows in results().values():
        for row in rows:
            lo, hi = row["ci95"]
            if row["verdict"] == "no clear difference":
                assert lo <= 0 <= hi
            else:
                assert lo > 0 or hi < 0


def test_the_committed_report_matches_the_script():
    committed = (ROOT / "results" / "paired_comparison.md").read_text(encoding="utf8").replace("\r\n", "\n")
    assert committed == "\n".join(pc.render(results())) + "\n"
