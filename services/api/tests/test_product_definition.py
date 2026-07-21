"""Product-definition regression guard.

Naismith's product definition was corrected from an interview agent to a
general-purpose, constitutionally bounded personal AI operating system. This
test pins that definition at the top of the README so interview-centered
framing cannot silently creep back into the canonical description.

It checks intent, not exact prose: the README's opening definition must be
general-purpose and must not be interview-framed, and the explicit scope guards
("not primarily an interview agent", "not basketball-focused") must remain.
Everything else in the README is free to mention interviews as one optional
future workflow.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_README = _REPO_ROOT / "README.md"


def _readme_text() -> str:
    return _README.read_text(encoding="utf-8")


def _opening_definition(text: str) -> str:
    """Return the first non-heading, non-empty prose block, lowercased.

    This is the canonical top-level description — the first thing a reader (or
    another agent) sees when deciding what Naismith is.
    """
    block: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if not stripped:
            if block:
                break
            continue
        block.append(stripped)
    return " ".join(block).lower()


def test_readme_opening_defines_naismith_as_general_purpose() -> None:
    opening = _opening_definition(_readme_text())
    assert "general-purpose" in opening, (
        "README's opening definition must describe Naismith as general-purpose; "
        f"got: {opening!r}"
    )


def test_readme_opening_is_not_interview_framed() -> None:
    opening = _opening_definition(_readme_text())
    assert "interview" not in opening, (
        "README's opening definition must not frame Naismith as an interview "
        f"agent; interviews are one optional future workflow, not the identity. "
        f"Opening was: {opening!r}"
    )


def test_readme_keeps_scope_guards() -> None:
    text = _readme_text().lower()
    for guard in ("not primarily an interview agent", "not basketball-focused"):
        assert guard in text, f"README is missing the scope guard: {guard!r}"
