"""Append-only audit store (Article XII), backed by the durable database.

Article XII requires significant actions to create append-only audit events
carrying actor, session, versions, and result state, while avoiding
unnecessary sensitive content (XII.3). Content is never stored raw — callers
pass pre-computed digests / safe summaries.

This is a thin facade over ``AuditRepository`` so the rest of the system keeps
depending on ``AuditStore.record``/``list`` while the system of record is now
the database (SQLite locally, Postgres in the hosted stack). The audit table is
insert-only: events are appended, never updated or deleted.
"""

from __future__ import annotations

import hashlib

from .db import Database
from .repositories import AuditRepository
from .schemas import AuditEvent


def digest(text: str) -> str:
    """SHA-256 hex digest of text, for storing a reference instead of content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AuditStore:
    def __init__(self, db: Database) -> None:
        self._repo = AuditRepository(db)

    def record(self, event: AuditEvent) -> AuditEvent:
        return self._repo.record(event)

    def list(self, session_id: str | None = None) -> list[AuditEvent]:
        return self._repo.list(session_id=session_id)
