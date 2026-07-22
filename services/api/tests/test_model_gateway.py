"""Model gateway (PR C): routing, selection, resilience, cost — mock-backed.

None of these tests make a network call or incur paid usage. The Anthropic
adapter is asserted to be inert (it never calls out), and every other provider
here is a local fake.
"""

from __future__ import annotations

import time

import pytest

from naismith_api.model_gateway import (
    AnthropicModelAdapter,
    MockModelAdapter,
    ModelGateway,
    ModelResult,
    ModelUsage,
    ProviderCallError,
    ProviderNotConfiguredError,
    ProviderTimeoutError,
    UnknownProviderError,
)


def _providers() -> dict[str, object]:
    return {
        "mock": MockModelAdapter(),
        "anthropic": AnthropicModelAdapter(api_key=None, model="claude-opus-4-8"),
    }


def test_model_usage_total() -> None:
    assert ModelUsage(prompt_tokens=3, completion_tokens=4).total_tokens == 7


def test_gateway_routes_to_default_and_reports_usage_and_cost() -> None:
    gw = ModelGateway(_providers(), default_provider="mock")
    result = gw.generate("hello")
    assert result.provider == "mock"
    assert result.model_version == MockModelAdapter.MODEL_VERSION
    assert result.usage.total_tokens >= 1
    assert result.cost_usd == 0.0  # the mock is free.


def test_gateway_unknown_provider_raises() -> None:
    gw = ModelGateway(_providers(), default_provider="mock")
    with pytest.raises(UnknownProviderError):
        gw.generate("hi", provider="does-not-exist")


def test_gateway_unknown_default_rejected_at_construction() -> None:
    with pytest.raises(UnknownProviderError):
        ModelGateway({"mock": MockModelAdapter()}, default_provider="nope")


def test_anthropic_is_inert_without_key() -> None:
    adapter = AnthropicModelAdapter(api_key=None, model="claude-opus-4-8")
    assert adapter.is_configured is False
    with pytest.raises(ProviderNotConfiguredError):
        adapter.generate("hi")


def test_anthropic_is_inert_even_with_key() -> None:
    # Configured != live: a key present still does not enable a call this phase.
    adapter = AnthropicModelAdapter(api_key="not-a-real-key", model="claude-opus-4-8")
    assert adapter.is_configured is True
    with pytest.raises(ProviderNotConfiguredError):
        adapter.generate("hi")


def test_gateway_default_anthropic_fails_fast() -> None:
    gw = ModelGateway(_providers(), default_provider="anthropic")
    with pytest.raises(ProviderNotConfiguredError):
        gw.generate("hi")


def test_anthropic_cost_math_uses_opus_list_price() -> None:
    adapter = AnthropicModelAdapter(api_key=None, model="claude-opus-4-8")
    # 1M input @ $5 + 1M output @ $25 = $30.
    cost = adapter.estimate_cost(
        ModelUsage(prompt_tokens=1_000_000, completion_tokens=1_000_000)
    )
    assert cost == pytest.approx(30.0)


class _Boom:
    name = "boom"
    model_version = "boom-1"

    def generate(self, prompt: str) -> ModelResult:
        raise RuntimeError("kaboom")


def test_gateway_normalizes_provider_errors() -> None:
    gw = ModelGateway({"boom": _Boom()}, default_provider="boom", max_retries=1)
    with pytest.raises(ProviderCallError):
        gw.generate("hi")


class _Slow:
    name = "slow"
    model_version = "slow-1"

    def generate(self, prompt: str) -> ModelResult:
        time.sleep(0.2)
        return ModelResult(text="late", model_version="slow-1")


def test_gateway_enforces_timeout() -> None:
    gw = ModelGateway(
        {"slow": _Slow()}, default_provider="slow", timeout_seconds=0.03, max_retries=0
    )
    with pytest.raises(ProviderTimeoutError):
        gw.generate("hi")


class _Flaky:
    name = "flaky"
    model_version = "flaky-1"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> ModelResult:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient")
        return ModelResult(text="recovered", model_version="flaky-1")


def test_gateway_retries_then_succeeds() -> None:
    flaky = _Flaky()
    gw = ModelGateway({"flaky": flaky}, default_provider="flaky", max_retries=1)
    result = gw.generate("hi")
    assert result.text == "recovered"
    assert flaky.calls == 2
