"""Session store and the text-conversation orchestrator.

Ties the slice together: a message flows user turn -> policy check -> mock model
-> assistant turn -> audit event. State is in-memory (no persistence, no durable
memory) which is correct for this phase — durable, governed memory is Phase 3.
"""

from __future__ import annotations

import threading

from . import audit as audit_mod
from .audit import AuditStore
from .model_gateway import ModelProvider
from .policy import POLICY_VERSION, evaluate_conversation_turn
from .schemas import (
    AuditEvent,
    CreateSessionRequest,
    MessageResponse,
    Session,
    SessionStatus,
    Speaker,
    Turn,
)


class SessionNotFoundError(KeyError):
    pass


class SessionStore:
    def __init__(self, model: ModelProvider, audit: AuditStore) -> None:
        self._model = model
        self._audit = audit
        self._lock = threading.Lock()
        self._sessions: dict[str, Session] = {}
        self._turns: dict[str, list[Turn]] = {}
        # One lock per session serializes that session's turns (see
        # handle_message). Guarded for creation by the store-wide _lock.
        self._session_locks: dict[str, threading.Lock] = {}

    def create(self, req: CreateSessionRequest) -> Session:
        session = Session(
            workspace_id=req.workspace_id,
            mode=req.mode,
            policy_version=POLICY_VERSION,
            model_route=self._model.model_version,
        )
        with self._lock:
            self._sessions[session.id] = session
            self._turns[session.id] = []
            self._session_locks[session.id] = threading.Lock()
        self._audit.record(
            AuditEvent(
                session_id=session.id,
                actor_type="user",
                actor_id="local-user",
                event_type="session.created",
                policy_version=POLICY_VERSION,
                status="ok",
            )
        )
        return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    def _session_lock(self, session_id: str) -> threading.Lock:
        with self._lock:
            lock = self._session_locks.get(session_id)
        if lock is None:
            raise SessionNotFoundError(session_id)
        return lock

    def _append_turn(self, session_id: str, speaker: Speaker, text: str) -> Turn:
        with self._lock:
            turns = self._turns[session_id]
            turn = Turn(
                session_id=session_id,
                sequence_number=len(turns),
                speaker=speaker,
                text=text,
            )
            turns.append(turn)
        return turn

    def handle_message(self, session_id: str, text: str) -> MessageResponse:
        session = self.get(session_id)
        if session.status is not SessionStatus.ACTIVE:
            raise SessionNotFoundError(session_id)

        # Serialize turns within a single session so an assistant reply always
        # immediately follows its triggering user turn, even under concurrent
        # requests to the same session. Different sessions still run in
        # parallel (each has its own lock). When a real, slow model replaces the
        # instant mock, revisit this with an async per-session queue so a busy
        # session doesn't block a worker thread.
        with self._session_lock(session_id):
            user_turn = self._append_turn(session_id, Speaker.USER, text)

            # Deterministic policy check, outside the model. A text turn
            # exercises no tool authority; the untrusted message text is never
            # passed to the authorization decision (see policy.py).
            decision = evaluate_conversation_turn()

            result = self._model.generate(text)
            assistant_turn = self._append_turn(session_id, Speaker.ASSISTANT, result.text)

            event = self._audit.record(
                AuditEvent(
                    session_id=session_id,
                    actor_type="agent",
                    actor_id="orchestrator",
                    event_type="message.exchanged",
                    policy_version=decision.policy_version,
                    model_version=result.model_version,
                    input_digest=audit_mod.digest(text),
                    result_digest=audit_mod.digest(result.text),
                    status="ok",
                    correlation_id=user_turn.id,
                )
            )

        return MessageResponse(
            session_id=session_id,
            user_turn=user_turn,
            assistant_turn=assistant_turn,
            policy_decision=decision,
            model_version=result.model_version,
            audit_event_id=event.id,
        )
