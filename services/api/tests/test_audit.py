from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from naismith_api.audit import AuditStore
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


def test_audit_log_is_append_only_on_disk(client: TestClient) -> None:
    settings = client.app.state.settings  # type: ignore[attr-defined]
    session_id = client.post("/v1/sessions", json={}).json()["id"]
    client.post(f"/v1/sessions/{session_id}/messages", json={"text": "one"})
    client.post(f"/v1/sessions/{session_id}/messages", json={"text": "two"})

    lines = settings.audit_log_path.read_text(encoding="utf-8").strip().splitlines()
    # 1 session.created + 2 message.exchanged
    assert len(lines) == 3


def test_audit_trail_survives_restart(tmp_path: Path) -> None:
    path = tmp_path / "audit" / "events.jsonl"
    store = AuditStore(path)
    store.record(
        AuditEvent(actor_type="user", actor_id="u", event_type="session.created", status="ok")
    )
    store.record(
        AuditEvent(actor_type="agent", actor_id="o", event_type="message.exchanged", status="ok")
    )

    # Simulate a restart: a fresh store over the same on-disk log must replay
    # the prior events, not surface an empty trail (Article XII).
    reopened = AuditStore(path)
    events = reopened.list()
    assert [e.event_type for e in events] == ["session.created", "message.exchanged"]
