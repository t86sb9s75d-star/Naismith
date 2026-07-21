"""Governance surface: make the active law inspectable at runtime.

Article XII (auditability/explainability) and the product principle
"human-readable by default" require that the governing Constitution and its
enforceable test registry are always visible. This module loads them from disk
so a running instance can answer "what rules are you operating under right now?"
"""

from __future__ import annotations

import hashlib
import re

import yaml

from .config import Settings
from .schemas import (
    ConstitutionalTestCase,
    ConstitutionalTestRegistry,
    ConstitutionInfo,
)

_VERSION_RE = re.compile(r"^version:\s*(.+?)\s*$", re.MULTILINE)
_ARTICLE_RE = re.compile(r"^##\s+Article\s+[IVXLC]+\b", re.MULTILINE)


def _parse_version(text: str) -> str:
    match = _VERSION_RE.search(text)
    if not match:
        raise ValueError("Constitution front matter is missing a `version` field")
    return match.group(1).strip()


def load_constitution(settings: Settings) -> ConstitutionInfo:
    path = settings.constitution_path
    text = path.read_text(encoding="utf-8")
    return ConstitutionInfo(
        version=_parse_version(text),
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        article_count=len(_ARTICLE_RE.findall(text)),
        source_path=str(path),
        text=text,
    )


def load_constitutional_tests(settings: Settings) -> ConstitutionalTestRegistry:
    raw = yaml.safe_load(settings.constitutional_tests_path.read_text(encoding="utf-8"))
    cases = [ConstitutionalTestCase(**case) for case in raw.get("cases", [])]
    return ConstitutionalTestRegistry(
        constitution_version=str(raw["constitution_version"]),
        cases=cases,
    )
