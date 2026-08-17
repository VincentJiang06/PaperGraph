"""Deterministic topic-file parser (parsing rules P1-P7, docs/01).

The parser is code, not judgment: it turns a Markdown topic file into the raw
material for a PaperSpec + ProjectContract. It records issues (missing /
duplicate / empty sections, ignored headings, stray non-list lines) for the
V-SPEC rules to consume; it never decides pass/fail itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Required section title (lowercased) -> canonical key.
REQUIRED_SECTIONS: dict[str, str] = {
    "topic": "topic",
    "core question": "core_question",
    "intended thesis": "intended_thesis",
    "paper type": "paper_type",
    "scope": "scope",
    "exclusions": "exclusions",
    "seed claims": "seed_claims",
    "known sources": "known_sources",
    "success criteria": "success_criteria",
}

# Canonical order used when reporting missing sections (topic-file order).
SECTION_ORDER: tuple[str, ...] = (
    "topic", "core_question", "intended_thesis", "paper_type", "scope",
    "exclusions", "seed_claims", "known_sources", "success_criteria",
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_LIST_MARKER_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$")

# Structured scope keys (P6), case-insensitive on the key text.
_SCOPE_KEYS = {"period", "region", "actors", "mechanisms"}
_SCOPE_LINE_RE = re.compile(r"^\s*([A-Za-z]+)\s*:\s*(.*)$")


@dataclass
class ParsedTopic:
    sections: dict[str, str] = field(default_factory=dict)  # canonical key -> raw body
    duplicates: list[str] = field(default_factory=list)     # canonical keys seen >1x
    empty: list[str] = field(default_factory=list)          # present but whitespace-only
    warnings: list[str] = field(default_factory=list)

    @property
    def missing(self) -> list[str]:
        return [k for k in SECTION_ORDER if k not in self.sections]


def _split_heading_blocks(text: str) -> list[tuple[str, str]]:
    """Return [(heading_title, body)] for every ATX heading (any level).

    Content before the first heading is dropped (preamble). Body runs to the
    next heading or EOF (P2).
    """
    lines = text.splitlines()
    blocks: list[tuple[str, str]] = []
    current_title: str | None = None
    current_body: list[str] = []
    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            if current_title is not None:
                blocks.append((current_title, "\n".join(current_body)))
            current_title = m.group(2).strip()
            current_body = []
        else:
            if current_title is not None:
                current_body.append(line)
            # else: preamble before first heading -> ignored
    if current_title is not None:
        blocks.append((current_title, "\n".join(current_body)))
    return blocks


def parse_topic(text: str) -> ParsedTopic:
    """Parse a topic file into recognized sections + issues (P1-P4)."""
    result = ParsedTopic()
    seen: set[str] = set()
    for title, body in _split_heading_blocks(text):
        key = REQUIRED_SECTIONS.get(title.casefold())
        if key is None:
            result.warnings.append(f"ignored unrecognized heading: {title!r}")
            continue
        if key in seen:
            # P3: duplicated recognized heading -> ambiguous (V-SPEC-01)
            if key not in result.duplicates:
                result.duplicates.append(key)
            continue
        seen.add(key)
        result.sections[key] = body
        if not body.strip():
            result.empty.append(key)  # P4
    return result


def parse_list(body: str) -> tuple[list[str], list[str]]:
    """Parse a list-valued section body (P5). Returns (items, warnings)."""
    items: list[str] = []
    warnings: list[str] = []
    stray: list[str] = []
    for line in body.splitlines():
        m = _LIST_MARKER_RE.match(line)
        if m:
            items.append(m.group(1).strip())
        elif line.strip():
            stray.append(line.strip())
    if not items:
        stripped = body.strip()
        return ([stripped] if stripped else []), warnings
    if stray:
        warnings.append(f"ignored {len(stray)} stray non-list line(s) between list items")
    return items, warnings


def parse_scope(scope_items: list[str]) -> dict[str, object]:
    """Parse Scope list items into the structured scope object (P6).

    Actors/Mechanisms split on ',' (trimmed). Non-matching lines populate no
    structured key (they remain in in_scope verbatim, handled by the caller).
    """
    scope: dict[str, object] = {}
    for item in scope_items:
        m = _SCOPE_LINE_RE.match(item)
        if not m:
            continue
        key = m.group(1).casefold()
        value = m.group(2).strip()
        if key not in _SCOPE_KEYS:
            continue
        if key in ("actors", "mechanisms"):
            scope[key] = [p.strip() for p in value.split(",") if p.strip()]
        else:  # period / region
            scope[key] = value
    return scope
