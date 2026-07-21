# contracts

Shared, language-neutral schemas for values that cross the Naismith API
boundary. These JSON Schemas (draft 2020-12) are the source of truth; the
backend Pydantic models (`services/api/src/naismith_api/schemas.py`) and the web
app's TypeScript types (`apps/web/src/types.ts`) both mirror them.

Keeping the contract explicit — rather than importing types across the
Python/TypeScript boundary — is the deliberate approach from the handoff
(§8.2): "keep contracts explicit through OpenAPI, JSON Schema, or generated
types."

| Schema | Describes |
|---|---|
| `session.schema.json` | A conversation session (local-first; workspace optional). |
| `turn.schema.json` | A single user or assistant turn. |
| `policy_decision.schema.json` | A deterministic policy engine decision. |
| `audit_event.schema.json` | An append-only audit record (digests, not content). |

When a schema changes, update the Pydantic model and the TS types in the same
change, and add/adjust a contract test.
