"""Model gateway: a provider-independent boundary for model calls (handoff §11).

Nothing downstream depends on a concrete provider. The gateway owns a registry
of providers, explicit provider selection, a wall-clock timeout, bounded
retries, normalized errors, and per-call usage/cost accounting.

Safety boundary for this phase: only the deterministic **mock** adapter can
actually produce output. A real provider (Anthropic) is registered so the
routing, entitlement, and cost machinery is exercised end to end, but its
``generate`` is intentionally **inert** — it makes no network call and cannot
incur paid usage. Activating live calls is a separate, owner-authorized step
(add a key AND wire the request); see ``AnthropicModelAdapter``.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from typing import Protocol

# --- Errors (normalized) ------------------------------------------------------


class GatewayError(Exception):
    """Base for all gateway-normalized failures."""


class UnknownProviderError(GatewayError):
    """Selected provider name is not registered."""


class ProviderNotConfiguredError(GatewayError):
    """Provider cannot run (e.g. no API key, or live calls not enabled)."""


class ProviderTimeoutError(GatewayError):
    """Provider did not return within the wall-clock timeout."""


class ProviderCallError(GatewayError):
    """Provider raised while generating; carries a normalized message."""


# --- Result / usage -----------------------------------------------------------


@dataclass(frozen=True)
class ModelUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class ModelResult:
    text: str
    model_version: str
    provider: str = "mock"
    usage: ModelUsage = field(default_factory=ModelUsage)
    cost_usd: float = 0.0
    # Article V: the adapter attests it performed/fabricated no external action.
    claims_external_action: bool = False


class ModelProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model_version(self) -> str: ...

    def generate(self, prompt: str) -> ModelResult: ...


def estimate_tokens(text: str) -> int:
    """Cheap, deterministic token estimate (~4 chars/token). Good enough for
    usage plumbing until a real tokenizer arrives with a real provider."""
    return max(1, len(text) // 4)


# --- Adapters -----------------------------------------------------------------


class MockModelAdapter:
    """Deterministic, offline stand-in for a real LLM provider (free).

    Same input always yields the same output, keeping the slice and its tests
    reproducible. Responses are transparently marked as coming from the mock so
    no caller mistakes them for a real model or a real-world outcome.
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
    def name(self) -> str:
        return "mock"

    @property
    def model_version(self) -> str:
        return self.MODEL_VERSION

    def generate(self, prompt: str) -> ModelResult:
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        reply = self._REPLIES[digest[0] % len(self._REPLIES)]
        return ModelResult(
            text=reply,
            model_version=self.MODEL_VERSION,
            provider=self.name,
            usage=ModelUsage(
                prompt_tokens=estimate_tokens(prompt),
                completion_tokens=estimate_tokens(reply),
            ),
            cost_usd=0.0,  # the mock is free.
            claims_external_action=False,
        )


class AnthropicModelAdapter:
    """First real provider — structurally complete but INERT this phase.

    It exists so the gateway's routing, entitlement view, and cost math are
    exercised against a real provider shape. It deliberately makes **no network
    call**: ``generate`` always raises ``ProviderNotConfiguredError``. Wiring
    the live request (and thereby incurring paid usage) is a separate step that
    requires explicit owner authorization. The API key, when present, is read
    only to report configured/not-configured status — never logged, never
    embedded, never sent anywhere from here.
    """

    # Anthropic list price (USD per million tokens). Used by estimate_cost so
    # the cost path is real and tested even while calls are inert.
    _PRICE_PER_MTOK: dict[str, tuple[float, float]] = {
        # model: (input_per_mtok, output_per_mtok)
        "claude-opus-4-8": (5.0, 25.0),
    }

    def __init__(self, api_key: str | None, model: str) -> None:
        self._api_key = api_key or None
        self._model = model

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model_version(self) -> str:
        return self._model

    @property
    def is_configured(self) -> bool:
        """Whether a key is present. Configured != live: even configured, this
        phase does not make calls."""
        return self._api_key is not None

    def estimate_cost(self, usage: ModelUsage) -> float:
        price = self._PRICE_PER_MTOK.get(self._model)
        if price is None:
            return 0.0
        in_price, out_price = price
        return (
            usage.prompt_tokens / 1_000_000 * in_price
            + usage.completion_tokens / 1_000_000 * out_price
        )

    def generate(self, prompt: str) -> ModelResult:
        # Inert by design. No network, no paid usage. Distinguish "no key" from
        # "key present but live calls not enabled" for a clear operator signal.
        if self._api_key is None:
            raise ProviderNotConfiguredError(
                "anthropic provider has no API key configured"
            )
        raise ProviderNotConfiguredError(
            "anthropic live calls are not enabled in this phase; wiring the real "
            "request requires explicit owner authorization"
        )


# --- Gateway ------------------------------------------------------------------


class ModelGateway:
    """Routes model calls to registered providers with timeout, retry, and cost.

    Also satisfies the ``ModelProvider`` protocol (``name``/``model_version``/
    ``generate``) so it can be dropped in wherever a single provider was used —
    e.g. as the agent runtime's model — while adding routing and resilience.
    """

    def __init__(
        self,
        providers: dict[str, ModelProvider],
        default_provider: str,
        *,
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
    ) -> None:
        if default_provider not in providers:
            raise UnknownProviderError(
                f"default provider {default_provider!r} is not registered"
            )
        self._providers = dict(providers)
        self._default = default_provider
        self._timeout = timeout_seconds
        self._max_retries = max_retries

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(self._providers)

    @property
    def default_provider(self) -> str:
        return self._default

    @property
    def name(self) -> str:
        return self._providers[self._default].name

    @property
    def model_version(self) -> str:
        return self._providers[self._default].model_version

    def _resolve(self, provider: str | None) -> ModelProvider:
        name = provider or self._default
        try:
            return self._providers[name]
        except KeyError as exc:
            raise UnknownProviderError(f"unknown provider {name!r}") from exc

    def generate(self, prompt: str, *, provider: str | None = None) -> ModelResult:
        chosen = self._resolve(provider)
        attempts = self._max_retries + 1
        last_error: GatewayError | None = None

        for _ in range(attempts):
            try:
                return self._call_with_timeout(chosen, prompt)
            except ProviderNotConfiguredError:
                # A config error will not fix itself on retry — fail fast.
                raise
            except (ProviderTimeoutError, ProviderCallError) as exc:
                last_error = exc

        assert last_error is not None  # attempts >= 1
        raise last_error

    def _call_with_timeout(self, provider: ModelProvider, prompt: str) -> ModelResult:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(provider.generate, prompt)
            try:
                return future.result(timeout=self._timeout)
            except FuturesTimeoutError as exc:
                raise ProviderTimeoutError(
                    f"provider {provider.name!r} exceeded {self._timeout}s"
                ) from exc
            except GatewayError:
                raise
            except Exception as exc:  # normalize any provider-raised error
                raise ProviderCallError(
                    f"provider {provider.name!r} failed: {type(exc).__name__}"
                ) from exc
