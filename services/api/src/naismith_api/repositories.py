"""Repositories: the durable replacement for the in-memory dicts/lists.

Each repository opens a short-lived ORM session per operation (via
``Database.session_scope``) and converts between ORM rows and the typed Pydantic
schemas that cross the API boundary. Nothing outside this module touches the ORM
rows, so the rest of the system depends only on the schemas.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select

from .db import (
    AuditEventRow,
    Database,
    ModelCallRow,
    SessionRow,
    TurnRow,
)
from .schemas import AuditEvent, Session, SessionMode, SessionStatus, Speaker, Turn


def _utc(dt: datetime) -> datetime:
    """SQLite drops tzinfo; treat a naive value read back as UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


# --- Sessions & turns ---------------------------------------------------------


class SessionRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def add_session(self, session: Session) -> None:
        with self._db.session_scope() as s:
            s.add(
                SessionRow(
                    id=session.id,
                    workspace_id=session.workspace_id,
                    mode=session.mode.value,
                    status=session.status.value,
                    policy_version=session.policy_version,
                    model_route=session.model_route,
                    created_at=session.created_at,
                )
            )

    def get_session(self, session_id: str) -> Session | None:
        with self._db.session_scope() as s:
            row = s.get(SessionRow, session_id)
            if row is None:
                return None
            return Session(
                id=row.id,
                workspace_id=row.workspace_id,
                mode=SessionMode(row.mode),
                status=SessionStatus(row.status),
                created_at=_utc(row.created_at),
                policy_version=row.policy_version,
                model_route=row.model_route,
            )

    def next_sequence_number(self, session_id: str) -> int:
        with self._db.session_scope() as s:
            count = s.scalar(
                select(func.count()).select_from(TurnRow).where(
                    TurnRow.session_id == session_id
                )
            )
            return int(count or 0)

    def append_turn(self, turn: Turn) -> None:
        with self._db.session_scope() as s:
            s.add(
                TurnRow(
                    id=turn.id,
                    session_id=turn.session_id,
                    sequence_number=turn.sequence_number,
                    speaker=turn.speaker.value,
                    text=turn.text,
                    created_at=turn.created_at,
                )
            )

    def list_turns(self, session_id: str) -> list[Turn]:
        with self._db.session_scope() as s:
            rows = s.scalars(
                select(TurnRow)
                .where(TurnRow.session_id == session_id)
                .order_by(TurnRow.sequence_number)
            ).all()
            return [
                Turn(
                    id=r.id,
                    session_id=r.session_id,
                    sequence_number=r.sequence_number,
                    speaker=Speaker(r.speaker),
                    text=r.text,
                    created_at=_utc(r.created_at),
                )
                for r in rows
            ]


# --- Audit --------------------------------------------------------------------


class AuditRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def record(self, event: AuditEvent) -> AuditEvent:
        with self._db.session_scope() as s:
            s.add(
                AuditEventRow(
                    id=event.id,
                    timestamp=event.timestamp,
                    session_id=event.session_id,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    event_type=event.event_type,
                    policy_version=event.policy_version,
                    model_version=event.model_version,
                    prompt_version=event.prompt_version,
                    tool_name=event.tool_name,
                    authorization_ref=event.authorization_ref,
                    input_digest=event.input_digest,
                    result_digest=event.result_digest,
                    status=event.status,
                    error_code=event.error_code,
                    correlation_id=event.correlation_id,
                )
            )
        return event

    def list(self, session_id: str | None = None) -> list[AuditEvent]:
        with self._db.session_scope() as s:
            stmt = select(AuditEventRow).order_by(
                AuditEventRow.timestamp, AuditEventRow.id
            )
            if session_id is not None:
                stmt = stmt.where(AuditEventRow.session_id == session_id)
            rows = s.scalars(stmt).all()
            return [
                AuditEvent(
                    id=r.id,
                    timestamp=_utc(r.timestamp),
                    session_id=r.session_id,
                    actor_type=r.actor_type,
                    actor_id=r.actor_id,
                    event_type=r.event_type,
                    policy_version=r.policy_version,
                    model_version=r.model_version,
                    prompt_version=r.prompt_version,
                    tool_name=r.tool_name,
                    authorization_ref=r.authorization_ref,
                    input_digest=r.input_digest,
                    result_digest=r.result_digest,
                    status=r.status,
                    error_code=r.error_code,
                    correlation_id=r.correlation_id,
                )
                for r in rows
            ]


# --- Model-call cost / usage --------------------------------------------------


class ModelCallRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def record(
        self,
        *,
        call_id: str,
        session_id: str,
        turn_id: str | None,
        provider: str,
        model_version: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        created_at: datetime,
    ) -> None:
        with self._db.session_scope() as s:
            s.add(
                ModelCallRow(
                    id=call_id,
                    session_id=session_id,
                    turn_id=turn_id,
                    provider=provider,
                    model_version=model_version,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost_usd,
                    created_at=created_at,
                )
            )

    def total_cost(self, session_id: str) -> float:
        with self._db.session_scope() as s:
            total = s.scalar(
                select(func.coalesce(func.sum(ModelCallRow.cost_usd), 0.0)).where(
                    ModelCallRow.session_id == session_id
                )
            )
            return float(total or 0.0)
