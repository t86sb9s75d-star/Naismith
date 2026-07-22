"""Session store and the text-conversation orchestrator.

Ties the slice together: a message flows user turn -> agent runtime (policy
check + model gateway) -> assistant turn -> durable audit event, with per-turn
model cost/usage recorded. Sessions, turns, audit events, and model-call cost
are the durable system of record (SQLite locally, Postgres in the hosted stack);
only the per-session locks are process-local runtime state.
"""

from __future__ import annotations

import threading
from uuid import uuid4

from . import audit as audit_mod
from .agent_runtime import AgentRuntime, AgentState
from .audit import AuditStore
from .model_gateway import GatewayError, ModelProvider
from .policy import POLICY_VERSION, evaluate_conversation_turn, evaluate_tool_operation
from .repositories import ModelCallRepository, SessionRepository
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


class ModelUnavailableError(RuntimeError):
    """The selected model provider could not produce a result (normalized from
    a gateway error). The user turn is still recorded; no assistant turn is."""


class SessionStore:
    def __init__(
        self,
        model: ModelProvider,
        audit: AuditStore,
        sessions: SessionRepository,
        model_calls: ModelCallRepository,
    ) -> None:
        self._model = model
        self._audit = audit
        self._sessions = sessions
        self._model_calls = model_calls
        # Guards creation of per-session locks. Session/turn data itself is
        # durable in the repository, not in memory.
        self._lock = threading.Lock()
        # One lock per session serializes that session's turns (see
        # handle_message). Created lazily so sessions loaded from a prior
        # process (after restart) still get a lock on first use.
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
        self._sessions.add_session(session)
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
        session = self._sessions.get_session(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    def _session_lock(self, session_id: str) -> threading.Lock:
        # Get-or-create; the store-wide lock only guards this small map.
        with self._lock:
            lock = self._session_locks.get(session_id)
            if lock is None:
                lock = threading.Lock()
                self._session_locks[session_id] = lock
        return lock

    def _append_turn(self, session_id: str, speaker: Speaker, text: str) -> Turn:
        # Caller holds the per-session lock, so the sequence number read and the
        # append are race-free within a session.
        turn = Turn(
            session_id=session_id,
            sequence_number=self._sessions.next_sequence_number(session_id),
            speaker=speaker,
            text=text,
        )
        self._sessions.append_turn(turn)
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

            # Route the turn through the Hermes-style agent runtime (§10.3),
            # which runs the policy-checked state machine and calls the model
            # gateway. Tools are deny-by-default this phase (Article X.1); the
            # runtime degrades gracefully to plain conversation (Article XIII.6).
            try:
                agent_result = self._agent.run(
                    session_id=session_id,
                    user_text=text,
                    workspace_id=session.workspace_id,
                )
            except GatewayError as exc:
                # Normalize any provider failure into a durable audit record and
                # a clean domain error the API maps to 503. The user turn stays
                # recorded; there is simply no assistant turn for it.
                self._audit.record(
                    AuditEvent(
                        session_id=session_id,
                        actor_type="agent",
                        actor_id="orchestrator",
                        event_type="message.failed",
                        policy_version=POLICY_VERSION,
                        input_digest=audit_mod.digest(text),
                        status="error",
                        error_code=type(exc).__name__,
                        correlation_id=user_turn.id,
                    )
                )
                raise ModelUnavailableError(str(exc)) from exc

            # The policy decision is still recorded for the conversational turn
            # exactly as before (it always ALLOWs text conversation in this
            # phase).
            decision = evaluate_conversation_turn()

            assistant_turn = self._append_turn(
                session_id, Speaker.ASSISTANT, agent_result.response_text
            )

            # Durable per-turn cost/usage provenance (handoff §11).
            self._model_calls.record(
                call_id=str(uuid4()),
                session_id=session_id,
                turn_id=assistant_turn.id,
                provider=agent_result.provider,
                model_version=agent_result.model_version,
                prompt_tokens=agent_result.usage.prompt_tokens,
                completion_tokens=agent_result.usage.completion_tokens,
                cost_usd=agent_result.cost_usd,
                created_at=assistant_turn.created_at,
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

            session_cost = self._model_calls.total_cost(session_id)

        return MessageResponse(
            session_id=session_id,
            user_turn=user_turn,
            assistant_turn=assistant_turn,
            policy_decision=decision,
            model_version=agent_result.model_version,
            audit_event_id=event.id,
            provider=agent_result.provider,
            prompt_tokens=agent_result.usage.prompt_tokens,
            completion_tokens=agent_result.usage.completion_tokens,
            cost_usd=agent_result.cost_usd,
            session_cost_usd=session_cost,
        )
