from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from naismith_api.audit import AuditStore
from naismith_api.db import Database
from naismith_api.schemas import AuditEvent


def test_message_creates_audit_event_with_digests_not_content(client: TestClient) -> None:
    session_id = client.post("/v1/sessions", json={}).json()["id"]
    secret_text = "my sensitive message body"
    client.post(f"/v1/sessions/{session_id}/messages", json={"text": secret_text})

    events = client.get(
        "/v1/governance/audit-events", params={"session_id": session_id}
    ).json()

    # session.created + message.exchanged
    types = [e["event_type"] for e in events]
    assert "session.created" in types
    assert "message.exchanged" in types

    exchanged = next(e for e in events if e["event_type"] == "message.exchanged")
    assert exchanged["policy_version"] == "1.0.0"
    assert exchanged["model_version"] == "mock-adapter-0.1.0"
    # Article XII.3: raw content must not appear; only digests are stored.
    assert exchanged["input_digest"] and secret_text not in exchanged["input_digest"]
    serialized = str(events)
    assert secret_text not in serialized


def test_audit_events_recorded_once_per_action(client: TestClient) -> None:
    session_id = client.post("/v1/sessions", json={}).json()["id"]
    client.post(f"/v1/sessions/{session_id}/messages", json={"text": "one"})
    client.post(f"/v1/sessions/{session_id}/messages", json={"text": "two"})

    events = client.get(
        "/v1/governance/audit-events", params={"session_id": session_id}
    ).json()
    # 1 session.created + 2 message.exchanged, durably recorded.
    assert len(events) == 3


def test_audit_trail_survives_restart(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'audit.db'}"
    db = Database(url)
    db.create_all()
    store = AuditStore(db)
    store.record(
        AuditEvent(actor_type="user", actor_id="u", event_type="session.created", status="ok")
    )
    store.record(
        AuditEvent(actor_type="agent", actor_id="o", event_type="message.exchanged", status="ok")
    )

    # Simulate a restart: a fresh Database + store over the same on-disk file
    # must see the prior events, not an empty trail (Article XII).
    reopened = AuditStore(Database(url))
    events = reopened.list()
    assert [e.event_type for e in events] == ["session.created", "message.exchanged"]
