#!/usr/bin/env bash
# Run the full local check suite: API lint + types + tests (incl. the
# constitutional suite) and the web app typecheck + build. Mirrors CI.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "── API: ruff ────────────────────────────────────────────────"
( cd "$repo_root/services/api" && ruff check . )

echo "── API: mypy (strict) ──────────────────────────────────────"
( cd "$repo_root/services/api" && mypy src )

echo "── API: pytest + constitutional suite ──────────────────────"
( cd "$repo_root/services/api" && pytest )

echo "── Web: typecheck + build ──────────────────────────────────"
( cd "$repo_root/apps/web" && npm run build )

echo "✓ all checks passed"
