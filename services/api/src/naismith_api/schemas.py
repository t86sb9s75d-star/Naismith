"""Typed boundary schemas (Pydantic v2).

These mirror the shared JSON Schemas in `packages/contracts/` and the domain
model in the handoff (§9). Every value that crosses the API boundary is a typed
schema — no ad-hoc dicts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid4())


# --- Governance ---------------------------------------------------------------


class ConstitutionInfo(BaseModel):
    version: str
    sha256: str
    article_count: int
    source_path: str
    text: str


class ConstitutionalTestCase(BaseModel):
    id: str
    article: str
    status: Literal["enforced", "pending"]
    setup: str
    expected: str


class ConstitutionalTestRegistry(BaseModel):
    constitution_version: str
    cases: list[ConstitutionalTestCase]


# --- Policy -------------------------------------------------------------------


class PolicyDecisionType(StrEnum):
    ALLOW = "allow"
    ALLOW_WITH_CONFIRMATION = "allow_with_confirmation"
    DENY = "deny"


class PolicyDecision(BaseModel):
    decision: PolicyDecisionType
    policy_version: str
    reason: str
    rules_evaluated: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)


# --- Sessions & turns ---------------------------------------------------------


class Speaker(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class SessionMode(StrEnum):
    TEXT = "text"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class Turn(BaseModel):
    id: str = Field(default_factory=_uuid)
    session_id: str
    sequence_number: int
    speaker: Speaker
    text: str
    created_at: datetime = Field(default_factory=_now)
    safety_labels: list[str] = Field(default_factory=list)


class Session(BaseModel):
    id: str = Field(default_factory=_uuid)
    # Nullable by design: the slice is single-user / local-first. Multi-tenant
    # scoping is additive later without a schema break (handoff §14).
    workspace_id: str | None = None
    mode: SessionMode = SessionMode.TEXT
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=_now)
    policy_version: str
    model_route: str


# --- Audit --------------------------------------------------------------------


class AuditEvent(BaseModel):
    id: str = Field(default_factory=_uuid)
    timestamp: datetime = Field(default_factory=_now)
    session_id: str | None = None
    actor_type: str
    actor_id: str
    event_type: str
    policy_version: str | None = None
    model_version: str | None = None
    prompt_version: str | None = None
    tool_name: str | None = None
    authorization_ref: str | None = None
    # Digests / safe summaries, never raw payloads (Article XII.3).
    input_digest: str | None = None
    result_digest: str | None = None
    status: str
    error_code: str | None = None
    correlation_id: str = Field(default_factory=_uuid)


# --- API request / response bodies -------------------------------------------


class CreateSessionRequest(BaseModel):
    workspace_id: str | None = None
    mode: SessionMode = SessionMode.TEXT


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1)


class MessageResponse(BaseModel):
    session_id: str
    user_turn: Turn
    assistant_turn: Turn
    policy_decision: PolicyDecision
    model_version: str
    audit_event_id: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str = "naismith-api"
    version: str
    constitution_version: str
