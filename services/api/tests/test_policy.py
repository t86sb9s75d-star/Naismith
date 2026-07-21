from __future__ import annotations

from naismith_api.policy import (
    POLICY_VERSION,
    evaluate_conversation_turn,
    evaluate_tool_operation,
)
from naismith_api.schemas import PolicyDecisionType


def test_tools_are_denied_by_default() -> None:
    decision = evaluate_tool_operation("vault.write", "write", grants=None)
    assert decision.decision is PolicyDecisionType.DENY
    assert decision.policy_version == POLICY_VERSION
    assert "tool.deny_by_default" in decision.rules_evaluated


def test_empty_grants_still_deny() -> None:
    decision = evaluate_tool_operation("vault.search", "read", grants={})
    assert decision.decision is PolicyDecisionType.DENY


def test_conversation_turn_is_allowed_without_tool_authority() -> None:
    decision = evaluate_conversation_turn()
    assert decision.decision is PolicyDecisionType.ALLOW
    assert decision.policy_version == POLICY_VERSION
