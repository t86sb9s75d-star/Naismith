"""Hermes-style agent runtime (Phase 0/1 skeleton).

Per §10.3 of the governing handoff, the agent runtime:
  - receives a normalized task,
  - loads the active Constitution/policy profile,
  - assembles authorized context,
  - decides if tools are needed,
  - builds a bounded plan,
  - executes via the tool router (deny-by-default in this phase),
  - tracks cost/time/step budgets,
  - handles errors,
  - returns a result with provenance, and
  - emits audit events.

This module implements the full state machine and plan schema for the
Phase 0/1 slice. Tool execution is intentionally wired to the
deny-by-default policy engine (Article X) — no tool grants exist yet.
All state transitions are explicit and observable. The runtime degrades
gracefully to plain text conversation when tools are unavailable (Article
XIII.6).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .model_gateway import ModelUsage
from .schemas import PolicyDecisionType

# ---------------------------------------------------------------------------
# Runtime states (§10.3)
# ---------------------------------------------------------------------------


class AgentState(StrEnum):
    IDLE = "idle"
    RECEIVING = "receiving"
    PLANNING = "planning"
    AWAITING_PERMISSION = "awaiting_permission"
    EXECUTING = "executing"
    AWAITING_TOOL = "awaiting_tool"
    AWAITING_USER = "awaiting_user"
    SYNTHESIZING = "synthesizing"
    PROPOSING_MEMORY = "proposing_memory"
    COMPLETED = "completed"
    STOPPED_BY_POLICY = "stopped_by_policy"
    CANCELLED = "cancelled"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Plan schema (§10.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanStep:
    id: str
    action: str
    # Tool is None for conversational (non-tool) steps.
    tool: str | None = None


@dataclass(frozen=True)
class PlanBudgets:
    max_steps: int = 10
    max_seconds: float = 30.0
    max_cost_usd: float = 0.10


@dataclass(frozen=True)
class AgentPlan:
    goal: str
    scope: str
    steps: tuple[PlanStep, ...] = field(default_factory=tuple)
    budgets: PlanBudgets = field(default_factory=PlanBudgets)
    permissions: tuple[str, ...] = field(default_factory=tuple)
    stop_conditions: tuple[str, ...] = field(
        default_factory=lambda: (
            "policy_check_unavailable",
            "budget_exceeded",
            "repeated_failure",
        )
    )


# ---------------------------------------------------------------------------
# Tool invocation envelope (§10.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolInvocationEnvelope:
    tool: str
    operation: str
    purpose: str
    workspace_id: str | None
    session_id: str
    grant_id: str | None
    arguments: dict[str, Any]
    idempotency_key: str
    policy_version: str
    requested_by: str


# ---------------------------------------------------------------------------
# Runtime result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentResult:
    state: AgentState
    response_text: str
    plan: AgentPlan
    steps_executed: int
    elapsed_seconds: float
    # Article V: always carry provenance on what the response was based on.
    model_version: str
    policy_version: str
    # Provider + cost/usage provenance from the gateway (handoff §11).
    provider: str = ""
    usage: ModelUsage = field(default_factory=ModelUsage)
    cost_usd: float = 0.0
    tool_calls_attempted: int = 0
    tool_calls_denied: int = 0
    degraded_to_conversation: bool = False


# ---------------------------------------------------------------------------
# Agent runtime
# ---------------------------------------------------------------------------


class AgentRuntime:
    """Bounded, policy-checked agent runtime (Hermes-style, §10.3).

    In this Phase 0/1 slice the runtime:
    - orchestrates text conversation through explicit states,
    - builds a minimal conversational plan for each turn,
    - attempts no tools (deny-by-default; Article X.1),
    - degrades to plain conversation (Article XIII.6), and
    - tracks cost/time/step budgets.

    The state machine is explicit so that transitions are testable without
    mocking the model or the policy engine.
    """

    def __init__(
        self,
        model: Any,  # ModelProvider protocol
        policy_evaluator: Any,  # callable(tool, op, grants) -> PolicyDecision
        policy_version: str,
    ) -> None:
        self._model = model
        self._policy_evaluator = policy_evaluator
        self._policy_version = policy_version

    def run(
        self,
        session_id: str,
        user_text: str,
        workspace_id: str | None = None,
    ) -> AgentResult:
        """Execute one conversational turn through the full state machine."""
        start = time.monotonic()
        state = AgentState.IDLE
        steps_executed = 0
        tool_calls_attempted = 0
        tool_calls_denied = 0

        # IDLE -> RECEIVING
        state = AgentState.RECEIVING

        # RECEIVING -> PLANNING
        state = AgentState.PLANNING
        plan = self._build_plan(user_text, session_id)

        # PLANNING -> AWAITING_PERMISSION (check policy for any tools in plan)
        state = AgentState.AWAITING_PERMISSION
        for step in plan.steps:
            if step.tool is not None:
                tool_calls_attempted += 1
                decision = self._policy_evaluator(step.tool, step.action, grants=None)
                if decision.decision != PolicyDecisionType.ALLOW:
                    tool_calls_denied += 1
                    # Article X: deny-by-default; degrade gracefully (XIII.6).
                    # No tool grants exist in this phase.

        # AWAITING_PERMISSION -> EXECUTING (conversational step only)
        state = AgentState.EXECUTING
        steps_executed += 1

        if steps_executed > plan.budgets.max_steps:
            state = AgentState.STOPPED_BY_POLICY
            return AgentResult(
                state=state,
                response_text="[stopped: budget exceeded]",
                plan=plan,
                steps_executed=steps_executed,
                elapsed_seconds=time.monotonic() - start,
                model_version=self._model.model_version,
                policy_version=self._policy_version,
                tool_calls_attempted=tool_calls_attempted,
                tool_calls_denied=tool_calls_denied,
                degraded_to_conversation=True,
            )

        # EXECUTING -> AWAITING_TOOL (skipped: no tool grants this phase)
        # AWAITING_TOOL -> SYNTHESIZING (direct in text-only path)
        state = AgentState.SYNTHESIZING
        result = self._model.generate(user_text)

        elapsed = time.monotonic() - start
        if elapsed > plan.budgets.max_seconds:
            state = AgentState.STOPPED_BY_POLICY
            return AgentResult(
                state=state,
                response_text="[stopped: time budget exceeded]",
                plan=plan,
                steps_executed=steps_executed,
                elapsed_seconds=elapsed,
                model_version=result.model_version,
                policy_version=self._policy_version,
                provider=result.provider,
                usage=result.usage,
                cost_usd=result.cost_usd,
                tool_calls_attempted=tool_calls_attempted,
                tool_calls_denied=tool_calls_denied,
                degraded_to_conversation=True,
            )

        # SYNTHESIZING -> PROPOSING_MEMORY -> COMPLETED
        # Memory proposals are Phase 3; skip here (Article VII).
        state = AgentState.COMPLETED

        degraded = tool_calls_attempted > 0 and tool_calls_denied == tool_calls_attempted

        return AgentResult(
            state=state,
            response_text=result.text,
            plan=plan,
            steps_executed=steps_executed,
            elapsed_seconds=time.monotonic() - start,
            model_version=result.model_version,
            policy_version=self._policy_version,
            provider=result.provider,
            usage=result.usage,
            cost_usd=result.cost_usd,
            tool_calls_attempted=tool_calls_attempted,
            tool_calls_denied=tool_calls_denied,
            degraded_to_conversation=degraded,
        )

    def _build_plan(self, user_text: str, session_id: str) -> AgentPlan:
        """Build a minimal bounded plan for a conversational turn.

        In this phase the plan is always a single-step text response. Tool
        steps are not populated because no grant system exists yet (Article
        X.1). The plan still carries explicit budgets and stop conditions so
        the runtime behaves correctly if this code path is exercised at scale.
        """
        return AgentPlan(
            goal=f"Respond to conversational turn in session {session_id}",
            scope="text_conversation",
            steps=(
                PlanStep(
                    id="step_respond",
                    action="generate_text_response",
                    tool=None,  # No tool authority in Phase 0/1.
                ),
            ),
            budgets=PlanBudgets(max_steps=1, max_seconds=30.0, max_cost_usd=0.01),
            permissions=(),
            stop_conditions=(
                "policy_check_unavailable",
                "budget_exceeded",
                "repeated_failure",
            ),
        )
