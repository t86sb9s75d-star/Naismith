"""Static guards for the /raw collector script.

`collect_state.sh` promises a *read-only* snapshot of git + environment state.
These guards enforce that contract without executing it against a live repo: the
script must stay syntactically valid and must never invoke a mutating git
subcommand or a destructive shell command. If someone later adds a write to the
collector, this test fails loudly instead of a raw-handoff snapshot silently
mutating the repository it was meant to only observe.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COLLECTOR = _REPO_ROOT / ".claude" / "skills" / "raw" / "scripts" / "collect_state.sh"

# git subcommands that change repository, ref, index, working-tree, or remote
# state — none of these belong in a read-only snapshot.
_MUTATING_GIT = (
    "push", "commit", "add", "checkout", "switch", "reset", "restore",
    "rebase", "merge", "cherry-pick", "rm", "mv", "clean", "stash", "apply",
    "fetch", "pull", "tag", "config", "gc", "prune", "update-ref",
    "filter-branch", "worktree", "am", "revert",
)

# destructive shell commands that could delete or overwrite files.
_DESTRUCTIVE_SHELL = ("rm", "mv", "dd", "shred", "truncate", "mkfs")


def _collector_text() -> str:
    return _COLLECTOR.read_text(encoding="utf-8")


def test_collector_exists_and_is_executable() -> None:
    assert _COLLECTOR.is_file(), f"collector script missing at {_COLLECTOR}"
    assert _COLLECTOR.stat().st_mode & 0o100, "collector script is not executable"


def test_collector_is_syntactically_valid() -> None:
    result = subprocess.run(
        ["bash", "-n", str(_COLLECTOR)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"bash -n rejected collect_state.sh:\n{result.stderr}"


def test_collector_invokes_no_mutating_git() -> None:
    text = _collector_text()
    offenders = [
        verb for verb in _MUTATING_GIT if re.search(rf"git\s+{re.escape(verb)}\b", text)
    ]
    assert not offenders, (
        f"collect_state.sh must stay read-only but invokes mutating git: {offenders}"
    )


def test_collector_runs_no_destructive_shell() -> None:
    text = _collector_text()
    offenders = [
        cmd
        for cmd in _DESTRUCTIVE_SHELL
        if re.search(rf"(?:^|[|;&]|\s){re.escape(cmd)}\s", text, re.MULTILINE)
    ]
    assert not offenders, (
        f"collect_state.sh must not run destructive shell commands: {offenders}"
    )
