#!/usr/bin/env bash
# Read-only snapshot of repo + environment state for a raw handoff.
#
# Everything here is non-mutating: it reads git and the environment and prints a
# Markdown block. Fold the real output into the handoff instead of reporting
# state from (possibly stale) memory — that's the "faithful, verified" rule.
set -uo pipefail

echo "## Environment (verified $(date -u +%Y-%m-%dT%H:%M:%SZ))"
echo "- cwd: $(pwd)"
echo "- host: $(uname -srm 2>/dev/null || echo unknown)"
echo

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "## Git (verified)"
  echo "- branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  echo "- upstream: $(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo '(none)')"
  echo "- remotes:"
  git remote -v | sed 's/^/    /'
  echo "- status (short):"
  if [ -n "$(git status --short)" ]; then
    git status --short | sed 's/^/    /'
  else
    echo "    (clean)"
  fi
  echo "- recent commits:"
  git log --oneline -15 | sed 's/^/    /'
  echo "- unpushed vs upstream:"
  git log --oneline '@{u}..HEAD' 2>/dev/null | sed 's/^/    /' || echo "    (no upstream configured)"
else
  echo "## Git"
  echo "- not a git repository"
fi
