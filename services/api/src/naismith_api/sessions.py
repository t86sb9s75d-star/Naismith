"""Session store and the text-conversation orchestrator.

Ties the slice together: a message flows user turn -> policy check -> mock model
-> assistant turn -> audit event. State is in-memory (no persistence, no durable
memory) which is correct for this phase — durable, governed memory is Phase 3.
"""

from __future__ import annotations

import threading

from . import audit as audit_mod
from .agent_runtime import AgentRuntime, AgentState
from .audit import AuditStore
from .model_gateway import ModelProvider
from .policy import POLICY_VERSION, evaluate_conversation_turn, evaluate_tool_operation
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
        # Hermes-style agent runtime (§10.3): policy-checked, bounded, stateful.
        self._agent = AgentRuntime(
            model=model,
            policy_evaluator=evaluate_tool_operation,
            policy_version=POLICY_VERSION,
        )

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

            # Route the turn through the Hermes-style agent runtime (§10.3).
            # The runtime runs the full state machine: IDLE -> RECEIVING ->
            # PLANNING -> AWAITING_PERMISSION -> EXECUTING -> SYNTHESIZING ->
            # COMPLETED. Tools are deny-by-default in this phase (Article X.1);
            # the runtime degrades gracefully to plain conversation
            # (Article XIII.6).
            agent_result = self._agent.run(
                session_id=session_id,
                user_text=text,
                workspace_id=session.workspace_id,
            )

            # The policy decision is still recorded for the conversational turn
            # exactly as before (it always ALLOWs text conversation in this
            # phase).
            decision = evaluate_conversation_turn()

            assistant_turn = self._append_turn(
                session_id, Speaker.ASSISTANT, agent_result.response_text
            )

            # Audit the exchange. The agent result carries provenance (model
            # version, policy version, plan state) — exactly what Article XII
            # requires.
            event = self._audit.record(
                AuditEvent(
                    session_id=session_id,
                    actor_type="agent",
                    actor_id="orchestrator",
                    event_type="message.exchanged",
                    policy_version=agent_result.policy_version,
                    model_version=agent_result.model_version,
                    input_digest=audit_mod.digest(text),
                    result_digest=audit_mod.digest(agent_result.response_text),
                    status="ok" if agent_result.state is AgentState.COMPLETED else "degraded",
                    correlation_id=user_turn.id,
                )
            )

        return MessageResponse(
            session_id=session_id,
            user_turn=user_turn,
            assistant_turn=assistant_turn,
            policy_decision=decision,
            model_version=agent_result.model_version,
            audit_event_id=event.id,
        )
