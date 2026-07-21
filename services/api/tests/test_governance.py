from __future__ import annotations

from fastapi.testclient import TestClient


def test_constitution_is_surfaced(client: TestClient) -> None:
    resp = client.get("/v1/governance/constitution")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.0.0"
    assert body["article_count"] == 15
    assert len(body["sha256"]) == 64
    assert "The Naismith Constitution" in body["text"]


def test_constitutional_tests_registry_is_surfaced(client: TestClient) -> None:
    resp = client.get("/v1/governance/constitutional-tests")
    assert resp.status_code == 200
    body = resp.json()
    assert body["constitution_version"] == "1.0.0"
    ids = {case["id"] for case in body["cases"]}
    assert "policy_denies_by_default" in ids
    # Every case declares an enforcement status.
    assert all(case["status"] in {"enforced", "pending"} for case in body["cases"])


def test_health_and_governance_agree_on_constitution_version(client: TestClient) -> None:
    # Both endpoints must report the same active constitution version — they
    # serve the copy loaded once at startup, so they cannot diverge.
    health_version = client.get("/health").json()["constitution_version"]
    governance_version = client.get("/v1/governance/constitution").json()["version"]
    assert health_version == governance_version
