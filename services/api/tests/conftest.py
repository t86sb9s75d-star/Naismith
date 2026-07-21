from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from naismith_api.config import Settings
from naismith_api.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    # Use the real committed constitution + test registry, but an isolated,
    # throwaway audit log so tests never touch the shared dev log.
    return Settings(audit_log_path=tmp_path / "audit" / "events.jsonl")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
