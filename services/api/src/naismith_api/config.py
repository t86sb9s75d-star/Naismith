"""Runtime configuration.

Deliberately dependency-light: reads from the environment with safe local-first
defaults so the slice runs with zero configuration and no secrets. Nothing here
may carry a real credential (Article VI/X) — secret-bearing values default to
empty and are supplied by the environment at deploy time. In particular the
Anthropic key defaults to empty and is never written back anywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _repo_root() -> Path:
    # services/api/src/naismith_api/config.py -> repo root is 4 parents up.
    return Path(__file__).resolve().parents[4]


def _default_database_url() -> str:
    # Honor DATABASE_URL (docker-compose sets Postgres); else a local SQLite
    # file so the service runs with zero configuration.
    default_sqlite = f"sqlite:///{_repo_root() / '.naismith' / 'naismith.db'}"
    return os.environ.get("DATABASE_URL", default_sqlite)


def _anthropic_api_key() -> str:
    # Read but never persist. Accept the Naismith-scoped name first, then the
    # conventional one. Empty means "not configured" (provider stays inert).
    return os.environ.get("NAISMITH_ANTHROPIC_API_KEY") or os.environ.get(
        "ANTHROPIC_API_KEY", ""
    )


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: os.environ.get("NAISMITH_ENV", "development"))
    log_level: str = field(default_factory=lambda: os.environ.get("NAISMITH_LOG_LEVEL", "INFO"))

    # Where the governing constitution lives. Surfaced verbatim at
    # /v1/governance/constitution so the active law is always inspectable.
    constitution_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "NAISMITH_CONSTITUTION_PATH",
                str(_repo_root() / "constitution" / "NAISMITH_CONSTITUTION.md"),
            )
        )
    )
    constitutional_tests_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "NAISMITH_CONSTITUTIONAL_TESTS_PATH",
                str(_repo_root() / "constitution" / "constitutional_tests.yaml"),
            )
        )
    )

    # System of record. SQLite locally, Postgres in the hosted stack, via
    # DATABASE_URL. Sessions, turns, audit events, and model-call cost persist.
    database_url: str = field(default_factory=_default_database_url)

    # Model gateway (handoff §11): default provider plus resilience knobs.
    default_model_provider: str = field(
        default_factory=lambda: os.environ.get("NAISMITH_MODEL_PROVIDER", "mock")
    )
    model_timeout_seconds: float = field(
        default_factory=lambda: float(os.environ.get("NAISMITH_MODEL_TIMEOUT", "30"))
    )
    model_max_retries: int = field(
        default_factory=lambda: int(os.environ.get("NAISMITH_MODEL_MAX_RETRIES", "1"))
    )

    # First real provider. The key defaults to empty; even when set, live calls
    # are not enabled this phase (the adapter stays inert). Never logged/echoed.
    anthropic_api_key: str = field(default_factory=_anthropic_api_key)
    anthropic_model: str = field(
        default_factory=lambda: os.environ.get("NAISMITH_ANTHROPIC_MODEL", "claude-opus-4-8")
    )

    # CORS origins for the local web app. Comma-separated.
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip()
            for o in os.environ.get(
                "NAISMITH_CORS_ORIGINS", "http://localhost:5173"
            ).split(",")
            if o.strip()
        )
    )


def get_settings() -> Settings:
    return Settings()
