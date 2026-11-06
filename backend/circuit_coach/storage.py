"""Optional storage of learner state (PLAN S4-4).

The service is stateless by default: the caller sends the learner's state and gets the updated
state back. With `CIRCUIT_COACH_DB` set to a database URL, it also keeps each learner's latest
state and a log of every model step:

    CIRCUIT_COACH_DB=sqlite:///circuit_coach.db          a file next to the service
    CIRCUIT_COACH_DB=postgresql://user:pass@host/db       Barabari's database engine

The tables use only portable types (text, integers, JSON), so the same code runs on SQLite and
PostgreSQL. A request that names a `learner_id` and sends an empty state starts from the stored
state; a request that sends a state keeps working exactly as before.
"""

from __future__ import annotations

import os
import time

from sqlalchemy import JSON, BigInteger, Column, Integer, MetaData, String, Table, create_engine, insert, select, update
from sqlalchemy.engine import Engine as SqlEngine

from .engine import LearnerState

metadata = MetaData()

learner_states = Table(
    "learner_states",
    metadata,
    Column("learner_id", String(128), primary_key=True),
    Column("mastery", JSON, nullable=False),
    Column("observations", JSON, nullable=False),
    Column("tried", JSON, nullable=False),
    Column("updated_at", BigInteger, nullable=False),
)

model_steps = Table(
    "model_steps",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("learner_id", String(128), nullable=False, index=True),
    Column("step", String(64), nullable=False),  # endpoint name: onboarding, quiz-result, ...
    Column("model", String(32), nullable=False),
    Column("request", JSON, nullable=False),
    Column("recommendation", JSON),
    Column("created_at", BigInteger, nullable=False),
)


def _now_ms() -> int:
    return int(time.time() * 1000)


class Storage:
    def __init__(self, url: str):
        self.url = url
        self.db: SqlEngine = create_engine(url, future=True)
        metadata.create_all(self.db)

    @staticmethod
    def from_env() -> "Storage | None":
        url = os.environ.get("CIRCUIT_COACH_DB")
        return Storage(url) if url else None

    def load(self, learner_id: str) -> LearnerState | None:
        with self.db.connect() as c:
            row = c.execute(select(learner_states).where(learner_states.c.learner_id == learner_id)).mappings().first()
        if row is None:
            return None
        return LearnerState(dict(row["mastery"]), dict(row["observations"]), {k: list(v) for k, v in row["tried"].items()})

    def save(self, learner_id: str, state: LearnerState) -> None:
        values = {"mastery": state.mastery, "observations": state.observations, "tried": state.tried, "updated_at": _now_ms()}
        with self.db.begin() as c:
            done = c.execute(update(learner_states).where(learner_states.c.learner_id == learner_id).values(**values))
            if done.rowcount == 0:
                c.execute(insert(learner_states).values(learner_id=learner_id, **values))

    def log(self, learner_id: str, step: str, model: str, request: dict, recommendation: dict | None) -> None:
        with self.db.begin() as c:
            c.execute(
                insert(model_steps).values(
                    learner_id=learner_id, step=step, model=model, request=request, recommendation=recommendation, created_at=_now_ms()
                )
            )

    def history(self, learner_id: str) -> list[dict]:
        with self.db.connect() as c:
            rows = c.execute(select(model_steps).where(model_steps.c.learner_id == learner_id).order_by(model_steps.c.id)).mappings().all()
        return [dict(r) for r in rows]
