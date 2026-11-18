"""Optional storage of learner state (PLAN S4-4).

The service is stateless by default: the caller sends the learner's state and gets the updated
state back. With `CIRCUIT_COACH_DB` set to a database URL, it also keeps each learner's latest
state and a log of every model step:

    CIRCUIT_COACH_DB=sqlite:///circuit_coach.db          a file next to the service
    CIRCUIT_COACH_DB=postgresql://user:pass@host/db       Barabari's database engine

The tables use only portable types (text, integers, JSON), so the same code runs on SQLite and
PostgreSQL. A request that names a `learner_id` and sends an empty state starts from the stored
state; a request that sends a state keeps working exactly as before.

A request that carries a `request_id` (or a Barabari attempt, keyed by its attempt id) and is
sent again for the same learner returns the saved response and is not applied twice. The key is
unique per learner and step in the database, and the state and its log row are written in one
transaction, so copies that arrive at the same moment are applied once too. Reusing a key with a
different request is refused (the API answers 409).
"""

from __future__ import annotations

import hashlib
import json
import os
import time

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Engine as SqlEngine
from sqlalchemy.exc import IntegrityError

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
    Column("request_key", String(160), index=True),  # request_id, or a Barabari attempt id
    Column("request_hash", String(64)),  # fingerprint of the request, to spot a reused key
    Column("response", JSON),
    Column("created_at", BigInteger, nullable=False),
    # NULL keys never clash, so requests without a request_id are always logged.
    UniqueConstraint("learner_id", "step", "request_key", name="uq_model_steps_request"),
)


def fingerprint(request: dict) -> str:
    return hashlib.sha256(json.dumps(request, sort_keys=True, default=str).encode()).hexdigest()


class KeyReused(Exception):
    """A request_id already used for a different request by the same learner and step."""


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
        with self.db.begin() as c:
            self._save(c, learner_id, state)

    @staticmethod
    def _save(c: Connection, learner_id: str, state: LearnerState) -> None:
        values = {"mastery": state.mastery, "observations": state.observations, "tried": state.tried, "updated_at": _now_ms()}
        done = c.execute(update(learner_states).where(learner_states.c.learner_id == learner_id).values(**values))
        if done.rowcount == 0:
            c.execute(insert(learner_states).values(learner_id=learner_id, **values))

    def record(
        self,
        learner_id: str,
        state: LearnerState,
        step: str,
        model: str,
        request: dict,
        recommendation: dict | None,
        request_key: str | None,
        response: dict,
    ) -> dict | None:
        """Save the state and log the step in one transaction.

        Returns None when it was applied, or the saved response when a copy of the same request
        (same learner, step and key) got there first; in that case nothing here is written.
        """
        try:
            with self.db.begin() as c:
                c.execute(
                    insert(model_steps).values(
                        learner_id=learner_id,
                        step=step,
                        model=model,
                        request=request,
                        recommendation=recommendation,
                        request_key=request_key,
                        request_hash=fingerprint(request),
                        response=response,
                        created_at=_now_ms(),
                    )
                )
                self._save(c, learner_id, state)
        except IntegrityError:
            if request_key is None:
                raise
            return self.replay(learner_id, step, request_key, request)
        return None

    def log(
        self,
        learner_id: str,
        step: str,
        model: str,
        request: dict,
        recommendation: dict | None,
        request_key: str | None = None,
        response: dict | None = None,
    ) -> None:
        with self.db.begin() as c:
            c.execute(
                insert(model_steps).values(
                    learner_id=learner_id,
                    step=step,
                    model=model,
                    request=request,
                    recommendation=recommendation,
                    request_key=request_key,
                    request_hash=fingerprint(request),
                    response=response,
                    created_at=_now_ms(),
                )
            )

    def replay(self, learner_id: str, step: str, request_key: str, request: dict | None = None) -> dict | None:
        """The saved response of a request already applied, so a resent one is not applied twice.

        With `request` given, raises KeyReused when the key was used for a different request.
        """
        q = (
            select(model_steps.c.response, model_steps.c.request_hash)
            .where(model_steps.c.learner_id == learner_id, model_steps.c.step == step, model_steps.c.request_key == request_key)
            .order_by(model_steps.c.id)
        )
        with self.db.connect() as c:
            row = c.execute(q).first()
        if row is None:
            return None
        if request is not None and row[1] is not None and row[1] != fingerprint(request):
            raise KeyReused(request_key)
        return row[0]

    def steps(self) -> list[dict]:
        """Every logged model step, oldest first (used to estimate question difficulty)."""
        with self.db.connect() as c:
            rows = c.execute(select(model_steps).order_by(model_steps.c.id)).mappings().all()
        return [dict(r) for r in rows]

    def history(self, learner_id: str) -> list[dict]:
        with self.db.connect() as c:
            rows = c.execute(select(model_steps).where(model_steps.c.learner_id == learner_id).order_by(model_steps.c.id)).mappings().all()
        return [dict(r) for r in rows]
