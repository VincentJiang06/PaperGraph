"""The evidence matcher + request fingerprint (docs/04 §Memoized Search).

The matcher is intentionally dumb and deterministic (no embeddings in v1): its
misses cost one docs round-trip; its determinism buys reproducible packs. Both
functions cite ``textutil`` (docs/09 §0) — no improvised tokenizer here.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

from ..textutil import scope_compatible, tokens

_WHITESPACE_RE = re.compile(r"\s+")


# --- evidence matcher (DocsPack assembly, `docs build-pack`) -----------------


def _eu_haystack(eu: dict[str, Any]) -> set[str]:
    """tokens(EU.summary) ∪ tokens(EU.quote_or_paraphrase) ∪ tokens(join(can_cite_for))."""
    toks: set[str] = set()
    toks |= set(tokens(eu.get("summary", "") or ""))
    toks |= set(tokens(eu.get("quote_or_paraphrase", "") or ""))
    toks |= set(tokens(" ".join(eu.get("can_cite_for", []) or [])))
    return toks


def score(claim: str, eu: dict[str, Any]) -> int:
    """|tokens(claim) ∩ (tokens(summary) ∪ tokens(quote) ∪ tokens(can_cite_for))|."""
    return len(set(tokens(claim or "")) & _eu_haystack(eu))


def match(
    claim: str, target_scope: dict[str, Any] | None, evidence_units: list[dict[str, Any]]
) -> list[tuple[int, dict[str, Any]]]:
    """Return the included (score, EU) pairs for a target claim.

    include EU iff score(EU) >= 2 AND scope_compatible(EU.scope, target.scope);
    order by (score desc, evidence_id asc); no cap in v1 (graphs are small).
    """
    scored: list[tuple[int, dict[str, Any]]] = []
    for eu in evidence_units:
        s = score(claim, eu)
        if s >= 2 and scope_compatible(eu.get("scope", {}) or {}, target_scope or {}):
            scored.append((s, eu))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("evidence_id", "")))
    return scored


# --- request-level fingerprint (docs/04) ------------------------------------


def _fp_normalize(s: str) -> str:
    """NFC, lowercase, collapse whitespace (docs/04 fingerprint normalize)."""
    s = unicodedata.normalize("NFC", s).lower()
    s = _WHITESPACE_RE.sub(" ", s)
    return s.strip()


def fingerprint(need: str, search_hints: list[str] | None) -> str:
    """sha256 over normalize(need) + "\\n" + sorted normalized search_hints."""
    hints = sorted(_fp_normalize(h) for h in (search_hints or []))
    payload = _fp_normalize(need) + "\n" + "\n".join(hints)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
