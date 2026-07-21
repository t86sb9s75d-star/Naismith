# naismith-api

The API + session gateway for Naismith's Phase 0/1 vertical slice
(`docs/NAISMITH_CLAUDE_CODE_HANDOFF.md`, §14). It proves the governance
skeleton before any autonomy:

- **`GET /health`** — liveness + active constitution version.
- **`GET /v1/governance/constitution`** — the governing law, surfaced verbatim
  with its version and SHA-256.
- **`GET /v1/governance/constitutional-tests`** — the enforceable test registry.
- **`GET /v1/governance/audit-events`** — the append-only audit trail
  (optionally filtered by `session_id`).
- **`POST /v1/sessions`** — start a text session (local-first; workspace
  optional).
- **`POST /v1/sessions/{id}/messages`** — send text, get a deterministic mock
  reply, with a policy check and an audit event.

What's deliberately absent in this phase: real model/voice providers, durable
memory, external tools, and persistence. A deterministic **mock model adapter**
stands in for the model, a **deterministic policy engine** makes every
authorization decision outside the model (deny-by-default), and an append-only
**JSONL audit store** records significant actions with digests, not raw content.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e "services/api[dev]"      # from the repo root
naismith-api                            # serves on http://127.0.0.1:8000
```

## Test

```bash
cd services/api && python -m pytest
```

The suite includes `tests/test_constitution_suite.py`, which executes the
`enforced` cases from `constitution/constitutional_tests.yaml` as live
assertions and skips the `pending` ones.
