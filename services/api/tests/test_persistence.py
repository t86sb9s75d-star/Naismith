"""Persistence (PR A) + gateway integration (PR C) at the API boundary.

Proves that sessions, turns, audit events, and per-turn model-call cost are the
durable system of record — they survive a simulated restart (a fresh app over
the same SQLite file) — and that the gateway's provenance surfaces on the wire.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from naismith_api.config import Settings
from naismith_api.db import Database, ModelCallRow
from naismith_api.main import create_app


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    return Settings(database_url=f"sqlite:///{tmp_path / 'naismith.db'}", **overrides)


def test_session_and_audit_persist_across_restart(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    app1 = create_app(settings)
    with TestClient(app1) as c1:
        session_id = c1.post("/v1/sessions", json={}).json()["id"]
        c1.post(f"/v1/sessions/{session_id}/messages", json={"text": "hello"})

    # A brand-new app instance over the same database file — simulated restart.
    app2 = create_app(settings)
    with TestClient(app2) as c2:
        got = c2.get(f"/v1/sessions/{session_id}")
        assert got.status_code == 200
        assert got.json()["id"] == session_id

        events = c2.get(
            "/v1/governance/audit-events", params={"session_id": session_id}
        ).json()
        types = [e["event_type"] for e in events]
        assert types == ["session.created", "message.exchanged"]


def test_message_response_carries_provider_and_cost(client: TestClient) -> None:
    session_id = client.post("/v1/sessions", json={}).json()["id"]
    resp = client.post(
        f"/v1/sessions/{session_id}/messages", json={"text": "hi there"}
    ).json()
    assert resp["provider"] == "mock"
    assert resp["prompt_tokens"] >= 1
    assert resp["completion_tokens"] >= 1
    assert resp["cost_usd"] == 0.0
    assert resp["session_cost_usd"] == 0.0


def test_model_call_cost_is_persisted(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    app = create_app(settings)
    with TestClient(app) as c:
        session_id = c.post("/v1/sessions", json={}).json()["id"]
        c.post(f"/v1/sessions/{session_id}/messages", json={"text": "one"})
        c.post(f"/v1/sessions/{session_id}/messages", json={"text": "two"})

    # A separate connection over the same file sees the committed cost rows.
    db = Database(settings.database_url)
    with db.session_scope() as s:
        count = s.scalar(select(func.count()).select_from(ModelCallRow))
        total = s.scalar(select(func.coalesce(func.sum(ModelCallRow.cost_usd), 0.0)))
    assert count == 2
    assert total == 0.0  # the mock provider is free.


def test_providers_endpoint_lists_mock_live_and_anthropic_inert(client: TestClient) -> None:
    body = client.get("/v1/models/providers").json()
    assert body["default_provider"] == "mock"
    by_name = {p["name"]: p for p in body["providers"]}

    assert by_name["mock"]["live"] is True
    assert by_name["mock"]["is_default"] is True

    # The real provider is registered but inert and unconfigured by default.
    assert by_name["anthropic"]["live"] is False
    assert by_name["anthropic"]["configured"] is False
    assert by_name["anthropic"]["model_version"] == "claude-opus-4-8"


def test_inert_default_provider_returns_503_and_audits_failure(tmp_path: Path) -> None:
    settings = _settings(tmp_path, default_model_provider="anthropic")
    app = create_app(settings)
    with TestClient(app) as c:
        session_id = c.post("/v1/sessions", json={}).json()["id"]
        resp = c.post(f"/v1/sessions/{session_id}/messages", json={"text": "hi"})
        assert resp.status_code == 503

        events = c.get(
            "/v1/governance/audit-events", params={"session_id": session_id}
        ).json()
        types = [e["event_type"] for e in events]
        assert "message.failed" in types
        failed = next(e for e in events if e["event_type"] == "message.failed")
        assert failed["status"] == "error"
        assert failed["error_code"] == "ProviderNotConfiguredError"
