"""Append-only audit store (development).

Article XII requires significant actions to create append-only audit events
carrying actor, session, versions, and result state, while avoiding
unnecessary sensitive content (XII.3). This development implementation appends
JSON lines to a local file and mirrors them in memory for inspection. Content
is never stored raw — callers pass pre-computed digests / safe summaries.

A JSONL file is a stand-in for the durable, tamper-evident audit store that
Postgres will back in a later phase; the interface here is what the rest of the
system depends on.
"""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path

from .schemas import AuditEvent


def digest(text: str) -> str:
    """SHA-256 hex digest of text, for storing a reference instead of content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AuditStore:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._lock = threading.Lock()
        self._events: list[AuditEvent] = []
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_existing()

    def _load_existing(self) -> None:
        """Replay the append-only log so the audit trail survives restarts.

        ``list()`` reads the in-memory mirror, so without replaying the log a
        restart would surface an empty audit trail even though the on-disk log
        still holds prior events — which would defeat the point of an audit
        trail (Article XII). Postgres replaces this dev store in Phase 1.
        """
        if not self._log_path.exists():
            return
        with self._log_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line:
                    continue
                try:
                    self._events.append(AuditEvent.model_validate_json(line))
                except ValueError:
                    # A malformed / partially-written line must not crash
                    # startup; skip it and keep the rest of the trail.
                    continue

    def record(self, event: AuditEvent) -> AuditEvent:
        line = event.model_dump_json()
        with self._lock:
            # Append-only: open in append mode, never truncate or rewrite.
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            self._events.append(event)
        return event

    def list(self, session_id: str | None = None) -> list[AuditEvent]:
        with self._lock:
            events = list(self._events)
        if session_id is None:
            return events
        return [e for e in events if e.session_id == session_id]
