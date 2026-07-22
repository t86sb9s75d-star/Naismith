"""SQLAlchemy persistence: engine, ORM tables, and a small Database helper.

This is the system of record for workspaces, sessions, turns, audit events, and
model-call cost/usage. It defaults to a local SQLite file (zero-config,
local-first) and switches to Postgres — or any SQLAlchemy-supported backend —
via DATABASE_URL. No secrets are hard-coded: the URL is supplied by the
environment (docker-compose provides the Postgres URL for the hosted stack).

Raw payloads are never stored in the audit table — callers pass pre-computed
digests / safe summaries (Article XII.3), exactly as the JSONL dev store did.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.types import DateTime


class Base(DeclarativeBase):
    pass


class WorkspaceRow(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    # Nullable by design: single-user / local-first. Tenant scoping is additive.
    workspace_id: Mapped[str | None] = mapped_column(String(64), index=True)
    mode: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    policy_version: Mapped[str] = mapped_column(String(64))
    model_route: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TurnRow(Base):
    __tablename__ = "turns"
    __table_args__ = (UniqueConstraint("session_id", "sequence_number"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.id"), index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditEventRow(Base):
    """Append-only audit trail (Article XII). Insert-only: never updated."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True)
    actor_type: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[str] = mapped_column(String(128))
    event_type: Mapped[str] = mapped_column(String(64))
    policy_version: Mapped[str | None] = mapped_column(String(64))
    model_version: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    tool_name: Mapped[str | None] = mapped_column(String(128))
    authorization_ref: Mapped[str | None] = mapped_column(String(128))
    input_digest: Mapped[str | None] = mapped_column(String(128))
    result_digest: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    error_code: Mapped[str | None] = mapped_column(String(64))
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)


class ModelCallRow(Base):
    """Per-turn model-call provenance: which provider, and what it cost.

    Cost/usage lives here rather than on the contract-guarded audit event, so
    the audit schema stays stable while every real model call still leaves a
    durable, queryable cost record (handoff §11: cost per turn/task).
    """

    __tablename__ = "model_calls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    turn_id: Mapped[str | None] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(128))
    prompt_tokens: Mapped[int] = mapped_column(Integer)
    completion_tokens: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _connect_args(url: str) -> dict[str, object]:
    # SQLite is accessed from FastAPI/TestClient worker threads; allow it.
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


class Database:
    """Owns the engine and hands out short-lived sessions.

    A repository opens a session per operation via ``session_scope`` so no ORM
    session is shared across threads — the app's per-session lock still
    serializes same-conversation writes.
    """

    def __init__(self, url: str) -> None:
        self._url = url
        self._ensure_sqlite_dir(url)
        self._engine: Engine = create_engine(
            url,
            future=True,
            connect_args=_connect_args(url),
        )
        self._session_factory = sessionmaker(
            bind=self._engine, expire_on_commit=False, future=True
        )

    @staticmethod
    def _ensure_sqlite_dir(url: str) -> None:
        if not url.startswith("sqlite") or ":memory:" in url:
            return
        path_part = url.split("sqlite:///", 1)[-1]
        if path_part:
            Path(path_part).expanduser().parent.mkdir(parents=True, exist_ok=True)

    @property
    def url(self) -> str:
        return self._url

    @property
    def engine(self) -> Engine:
        return self._engine

    def create_all(self) -> None:
        """Create tables if absent. Alembic owns migrations in deployment; this
        keeps local/dev and tests zero-config."""
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
