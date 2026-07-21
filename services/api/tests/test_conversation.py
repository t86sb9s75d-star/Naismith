from __future__ import annotations

from fastapi.testclient import TestClient


def _new_session(client: TestClient) -> str:
    resp = client.post("/v1/sessions", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["policy_version"] == "1.0.0"
    assert body["model_route"] == "mock-adapter-0.1.0"
    # Local-first: no workspace required.
    assert body["workspace_id"] is None
    return str(body["id"])


def test_full_text_exchange(client: TestClient) -> None:
    session_id = _new_session(client)
    resp = client.post(
        f"/v1/sessions/{session_id}/messages",
        json={"text": "Hello Naismith"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == session_id
    assert body["user_turn"]["speaker"] == "user"
    assert body["assistant_turn"]["speaker"] == "assistant"
    assert body["assistant_turn"]["sequence_number"] == 1
    assert body["policy_decision"]["decision"] == "allow"
    assert body["model_version"] == "mock-adapter-0.1.0"
    assert body["audit_event_id"]


def test_mock_adapter_is_deterministic(client: TestClient) -> None:
    a = _new_session(client)
    b = _new_session(client)
    reply_a = client.post(f"/v1/sessions/{a}/messages", json={"text": "same prompt"})
    reply_b = client.post(f"/v1/sessions/{b}/messages", json={"text": "same prompt"})
    assert reply_a.json()["assistant_turn"]["text"] == reply_b.json()["assistant_turn"]["text"]


def test_unknown_session_is_404(client: TestClient) -> None:
    resp = client.post("/v1/sessions/does-not-exist/messages", json={"text": "hi"})
    assert resp.status_code == 404


def test_empty_message_is_rejected(client: TestClient) -> None:
    session_id = _new_session(client)
    resp = client.post(f"/v1/sessions/{session_id}/messages", json={"text": ""})
    assert resp.status_code == 422
