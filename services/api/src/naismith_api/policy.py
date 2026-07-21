"""Deterministic policy engine (stub).

Prompts are probabilistic; authorization is not. Per Article X, every
authorization decision is made here, in code, outside the language model. This
stub implements the invariants the Phase 0/1 slice can enforce:

* Tools are deny-by-default (X.1). With no grant system yet, every tool
  operation is denied.
* The engine fails closed (X.10): the decision function takes only the
  structured operation and the caller's grants — never message content — so
  untrusted/retrieved text is structurally incapable of changing a decision
  (X.4/X.5).
* Plain text conversation carries no tool authority and is allowed.

`POLICY_VERSION` is stamped onto every decision and every audit event so the
governing policy is always attributable (Article XII).
"""

from __future__ import annotations

from collections.abc import Mapping

from .schemas import PolicyDecision, PolicyDecisionType

POLICY_VERSION = "1.0.0"


def evaluate_conversation_turn() -> PolicyDecision:
    """A text-only conversational turn. No tool authority is exercised."""
    return PolicyDecision(
        decision=PolicyDecisionType.ALLOW,
        policy_version=POLICY_VERSION,
        reason="Text conversation carries no tool authority and is permitted.",
        rules_evaluated=["conversation.text.allowed"],
    )


def evaluate_tool_operation(
    tool: str,
    operation: str,
    grants: Mapping[str, object] | None = None,
) -> PolicyDecision:
    """Authorize a tool operation.

    Note the signature: this function is deliberately incapable of seeing user
    or retrieved content. It decides only from the structured (tool, operation)
    and the caller's explicit grants. In this phase there is no grant system, so
    the deny-by-default rule (Article X.1) applies to every operation, and the
    engine fails closed (X.10).
    """
    granted = bool(grants) and grants is not None and grants.get(tool) is not None
    if not granted:
        return PolicyDecision(
            decision=PolicyDecisionType.DENY,
            policy_version=POLICY_VERSION,
            reason=(
                f"No grant exists for tool '{tool}' operation '{operation}'. "
                "Tools are deny-by-default (Article X)."
            ),
            rules_evaluated=["tool.deny_by_default", "tool.requires_grant"],
            required_actions=["obtain_tool_grant"],
        )
    # Grants are not yet issuable in this phase; reaching here would be a bug.
    return PolicyDecision(
        decision=PolicyDecisionType.DENY,
        policy_version=POLICY_VERSION,
        reason="Grant issuance is not available in the current phase; failing closed.",
        rules_evaluated=["tool.grant_system_unavailable", "fail_closed"],
    )
