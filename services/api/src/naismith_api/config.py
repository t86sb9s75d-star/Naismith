"""Runtime configuration.

Deliberately dependency-light: reads from the environment with safe local-first
defaults so the slice runs with zero configuration and no secrets. Nothing here
may carry a real credential (Article VI/X) — secret-bearing values default to
empty and are supplied by the environment at deploy time.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _repo_root() -> Path:
    # services/api/src/naismith_api/config.py -> repo root is 4 parents up.
    return Path(__file__).resolve().parents[4]


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

    # Append-only development audit log. A local JSONL file stands in for the
    # durable audit store until Postgres lands; it is git-ignored.
    audit_log_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "NAISMITH_AUDIT_LOG_PATH",
                str(_repo_root() / ".naismith" / "audit" / "events.jsonl"),
            )
        )
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
