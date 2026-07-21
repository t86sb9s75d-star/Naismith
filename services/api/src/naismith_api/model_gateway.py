"""Model gateway with a mock adapter.

The gateway normalizes model calls behind a provider-independent interface
(handoff §11.1) so no downstream code depends on a concrete provider. This
phase ships only a deterministic mock adapter: no provider key, no network, and
— per Article V — output that is explicitly labeled as generated and never
claims a completed external action or fabricated tool result.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelResult:
    text: str
    model_version: str
    # Article V: the adapter attests it has not performed or fabricated any
    # external action or tool result.
    claims_external_action: bool = False


class ModelProvider(Protocol):
    def generate(self, prompt: str) -> ModelResult: ...

    @property
    def model_version(self) -> str: ...


class MockModelAdapter:
    """Deterministic, offline stand-in for a real LLM provider.

    Same input always yields the same output, which keeps the vertical slice
    and its tests reproducible. Responses are transparently marked as coming
    from the mock adapter so no caller can mistake them for a real model or a
    real-world outcome.
    """

    MODEL_VERSION = "mock-adapter-0.1.0"

    _REPLIES = (
        "Noted. I'm Naismith running on a mock adapter, so this is a placeholder "
        "reply — no real model, tools, or memory are involved yet.",
        "Understood. This is a deterministic mock response from the Phase 0/1 "
        "slice; I have not taken any external action.",
        "Got it. The mock adapter is echoing a canned, governance-safe reply "
        "while the real model gateway is still stubbed.",
    )

    @property
    def model_version(self) -> str:
        return self.MODEL_VERSION

    def generate(self, prompt: str) -> ModelResult:
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        reply = self._REPLIES[digest[0] % len(self._REPLIES)]
        return ModelResult(
            text=reply,
            model_version=self.MODEL_VERSION,
            claims_external_action=False,
        )
