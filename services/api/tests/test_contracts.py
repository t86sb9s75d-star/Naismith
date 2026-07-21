"""Cross-boundary contract guards.

The shared JSON Schemas in packages/contracts/ are the source of truth for
boundary types. The API's Pydantic models and the web app's TypeScript types
must both mirror them. These tests catch drift in either direction — the exact
class of bug where a field exists in the schema and the Pydantic model but was
quietly dropped from the TypeScript mirror.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from naismith_api.schemas import AuditEvent

_REPO_ROOT = Path(__file__).resolve().parents[3]
_AUDIT_SCHEMA = _REPO_ROOT / "packages" / "contracts" / "audit_event.schema.json"
_WEB_TYPES = _REPO_ROOT / "apps" / "web" / "src" / "types.ts"


def _schema_properties() -> set[str]:
    schema = json.loads(_AUDIT_SCHEMA.read_text(encoding="utf-8"))
    return set(schema["properties"])


def test_pydantic_audit_event_matches_contract_schema() -> None:
    props = _schema_properties()
    fields = set(AuditEvent.model_fields)
    assert fields == props, (
        f"AuditEvent Pydantic/schema drift — "
        f"schema-only={sorted(props - fields)}, model-only={sorted(fields - props)}"
    )


def test_web_audit_event_type_includes_every_contract_field() -> None:
    props = _schema_properties()
    ts = _WEB_TYPES.read_text(encoding="utf-8")
    match = re.search(r"export interface AuditEvent\s*\{(.*?)\}", ts, re.DOTALL)
    assert match, "AuditEvent interface not found in apps/web/src/types.ts"
    ts_fields = set(re.findall(r"(\w+)\s*:", match.group(1)))
    missing = props - ts_fields
    assert not missing, f"web AuditEvent type is missing contract fields: {sorted(missing)}"
