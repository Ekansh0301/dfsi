"""Loader for EdNet KT1 (real student question logs from a Korean English-test tutoring app).

EdNet (Choi et al., 2020) is released under CC BY-NC 4.0 for research. Each student has one
CSV of answers (timestamp, question id, chosen option, time taken). `questions.csv` gives
the correct option and the concept tags of every question.

Why it is only a partial test for us: it has real answers and real concept tags, so it can
check how well BKT predicts a real learner's next answer. It has no prerequisite graph and no
hidden truth, so it cannot test root-cause finding. It also comes from a different subject,
language and population from our electrician learners.
"""

from __future__ import annotations

import pickle
import zipfile
from pathlib import Path

import numpy as np

from .prediction import Seq


def load_questions(path: Path) -> dict[str, tuple[str, tuple[str, ...]]]:
    """question id -> (correct option, concept tags)."""
    out: dict[str, tuple[str, tuple[str, ...]]] = {}
    with open(path, encoding="utf8") as f:
        header = f.readline().strip().split(",")
        i_q, i_c, i_t = header.index("question_id"), header.index("correct_answer"), header.index("tags")
        for line in f:
            parts = line.rstrip("\n").split(",")
            out[parts[i_q]] = (parts[i_c], tuple(parts[i_t].split(";")))
    return out


def load_sample(
    zip_path: Path,
    questions_path: Path,
    n_users: int = 40000,
    min_len: int = 30,
    max_len: int = 300,
    seed: int = 0,
    cache: Path | None = None,
) -> list[Seq]:
    """A random sample of students, each as a time-ordered list of answers.

    Students with fewer than `min_len` answers are dropped; longer ones are cut to their first
    `max_len` answers. The result is cached as a pickle because reading the zip takes a while.
    """
    if cache and cache.exists():
        return pickle.loads(cache.read_bytes())

    questions = load_questions(questions_path)
    rng = np.random.default_rng(seed)
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.endswith(".csv") and "__MACOSX" not in n]
        pick = rng.choice(len(names), size=min(n_users, len(names)), replace=False)
        seqs: list[Seq] = []
        for i in pick:
            rows = z.read(names[i]).decode().splitlines()[1:]
            parsed = []
            for line in rows:
                ts, _sid, qid, ans, _el = line.split(",")
                q = questions.get(qid)
                if q is None:
                    continue
                parsed.append((int(ts), qid, q[1], int(ans == q[0])))
            if len(parsed) < min_len:
                continue
            parsed.sort(key=lambda r: r[0])
            seqs.append([(qid, tags, y, False) for _, qid, tags, y in parsed[:max_len]])
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(pickle.dumps(seqs))
    return seqs
