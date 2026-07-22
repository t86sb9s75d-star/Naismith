"""Tests for the Hermes-style agent runtime (§10.3)."""

from __future__ import annotations

from naismith_api.agent_runtime import (
    AgentRuntime,
    AgentState,
    PlanBudgets,
    PlanStep,
    ToolInvocationEnvelope,
)
from naismith_api.model_gateway import MockModelAdapter
from naismith_api.policy import POLICY_VERSION, evaluate_tool_operation
from naismith_api.schemas import PolicyDecisionType


def _make_runtime() -> AgentRuntime:
    return AgentRuntime(
        model=MockModelAdapter(),
        policy_evaluator=evaluate_tool_operation,
        policy_version=POLICY_VERSION,
    )


def test_runtime_completes_conversational_turn() -> None:
    rt = _make_runtime()
    result = rt.run(session_id="s1", user_text="Hello Naismith")
    assert result.state is AgentState.COMPLETED
    assert result.response_text  # non-empty
    assert result.model_version == "mock-adapter-0.1.0"
    assert result.policy_version == POLICY_VERSION


def test_runtime_plan_is_bounded() -> None:
    rt = _make_runtime()
    result = rt.run(session_id="s2", user_text="plan me something")
    # Phase 0/1 plan: exactly one conversational step, no tools.
    assert result.plan.scope == "text_conversation"
    assert len(result.plan.steps) == 1
    assert result.plan.steps[0].tool is None
    assert result.plan.budgets.max_steps >= 1


def test_runtime_tool_calls_denied_by_default() -> None:
    """Article X.1: any tool in the plan must be denied with no grant system."""
    rt = _make_runtime()
    result = rt.run(session_id="s3", user_text="use a tool for me")
    # In Phase 0/1 the plan has no tool steps; tool_calls_attempted stays 0.
    assert result.tool_calls_attempted == 0
    assert result.tool_calls_denied == 0


def test_runtime_result_carries_provenance() -> None:
    """Article V: provenance fields must always be present on the result."""
    rt = _make_runtime()
    result = rt.run(session_id="s4", user_text="what do you know?")
    assert result.model_version
    assert result.policy_version
    assert result.elapsed_seconds >= 0


def test_runtime_deterministic_for_same_prompt() -> None:
    """MockModelAdapter guarantees determinism; the runtime must preserve it."""
    rt = _make_runtime()
    r1 = rt.run(session_id="s5", user_text="same prompt")
    r2 = rt.run(session_id="s6", user_text="same prompt")
    assert r1.response_text == r2.response_text


def test_plan_step_schema() -> None:
    step = PlanStep(id="step_1", action="generate_text_response", tool=None)
    assert step.id == "step_1"
    assert step.tool is None


def test_plan_budgets_defaults() -> None:
    budgets = PlanBudgets()
    assert budgets.max_steps > 0
    assert budgets.max_seconds > 0
    assert budgets.max_cost_usd > 0


def test_tool_invocation_envelope_schema() -> None:
    env = ToolInvocationEnvelope(
        tool="vault.search",
        operation="read",
        purpose="retrieve context",
        workspace_id=None,
        session_id="s7",
        grant_id=None,
        arguments={"query": "test"},
        idempotency_key="idem-1",
        policy_version=POLICY_VERSION,
        requested_by="orchestrator",
    )
    assert env.tool == "vault.search"
    assert env.grant_id is None  # no grants in this phase


def test_policy_evaluator_denies_tool_in_envelope() -> None:
    """The policy evaluator used by the runtime must deny any tool."""
    decision = evaluate_tool_operation("vault.search", "read", grants=None)
    assert decision.decision is PolicyDecisionType.DENY


def test_agent_state_enum_completeness() -> None:
    """All states from §10.3 must be present."""
    expected = {
        "idle", "receiving", "planning", "awaiting_permission",
        "executing", "awaiting_tool", "awaiting_user", "synthesizing",
        "proposing_memory", "completed", "stopped_by_policy",
        "cancelled", "failed",
    }
    actual = {s.value for s in AgentState}
    assert expected == actual
