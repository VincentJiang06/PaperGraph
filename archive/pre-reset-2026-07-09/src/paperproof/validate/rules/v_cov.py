"""V-COV: coverage ledger, saturation & role-profile floors (S4, docs/17).

These rules are DERIVED-state rules: the coverage ledger is a deterministic fold
(no canonical writer), so most are enforced by the fold itself and its consumers
(the committer's saturation branch, the freeze floors, the ContextPack coverage
block). This module gives each rule a testable home + the whole-project sweep hook.

    V-COV-01  ledger determinism: same canonical state => identical ledger
    V-COV-02  every ContextPack for a fact/mechanism/bridge target embeds the
              target's current ledger line
    V-COV-03  the committer consults saturation, never a request count; a
              born-dead re-proof carries reason="saturated" only, and only with
              the role floor unmet
    V-COV-04  freeze / MSA-4 / compiler floors follow the role-profile table;
              msa-check reports the per-node ledger line for every miss
    V-COV-05  a narrowed claim inherits the parent claim's ledger (rounds reset
              to 0 only if the narrowed core_terms change by more than half)
"""

from __future__ import annotations

import re
from typing import Any

from ..envelope import Failure

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "of", "in", "on", "and", "or", "to", "for", "by", "with",
    "is", "are", "was", "were", "as", "at", "how", "did", "into", "that", "this",
}


# --- V-COV-02: ContextPack coverage block -----------------------------------


def check_context_pack_coverage(ctx_pack: dict[str, Any]) -> list[Failure]:
    """V-COV-02: a ContextPack whose target is a fact/mechanism/bridge node must
    embed the target's coverage ledger line; other targets carry coverage=null."""
    target = ctx_pack.get("target") or {}
    is_node = "node_id" in target
    needs = is_node and (
        target.get("node_type") in ("fact", "mechanism")
        or (target.get("origin") or {}).get("kind") == "bridge"
    )
    cov = ctx_pack.get("coverage")
    if needs and not isinstance(cov, dict):
        return [Failure("V-COV-02", f"{ctx_pack.get('pack_id')}: fact/mechanism/bridge target lacks a coverage block")]
    if needs and cov.get("node_id") != target.get("node_id"):
        return [Failure("V-COV-02", f"{ctx_pack.get('pack_id')}: coverage block names the wrong node")]
    return []


# --- V-COV-03: born-dead reason -> saturated only ---------------------------

# The single born-dead reason S4 assigns a saturated needs_docs re-proof (D1).
# The committer builds its dead_letter detail from this constant so the string
# is never hand-typed (F13); floor_met (a second detail key) distinguishes the
# floor-unmet stop from the floor-met human-review case.
SATURATED = "saturated"


def check_born_dead_reason(reason: str, floor_met: bool | None = None) -> list[Failure]:
    """V-COV-03: the committer's only born-dead reason under S4 is 'saturated'
    (D1). ``floor_met`` (when supplied) must be a bool — it is the sole
    distinguisher between the two saturated stops, never a distinct reason."""
    failures: list[Failure] = []
    if reason != SATURATED:
        failures.append(Failure("V-COV-03", f"born-dead reason {reason!r} is not the saturated stop reason"))
    if floor_met is not None and not isinstance(floor_met, bool):
        failures.append(Failure("V-COV-03", f"born-dead floor_met {floor_met!r} is not a bool"))
    return failures


# --- V-COV-05: narrow-inheritance -------------------------------------------


def core_terms(text: str) -> set[str]:
    """The claim's core content terms (lower-cased alnum tokens minus stopwords)."""
    return {t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOP and len(t) > 2}


def rounds_reset_on_narrow(parent_claim: str, narrowed_claim: str) -> bool:
    """V-COV-05: a narrow inherits the parent's ledger; its rounds reset to 0 ONLY
    IF the narrowed claim's core_terms change by MORE THAN HALF (a materially
    different search target). Otherwise the prior search rounds still count."""
    old = core_terms(parent_claim)
    new = core_terms(narrowed_claim)
    if not old:
        return False
    dropped = old - new
    added = new - old
    changed = len(dropped) + len(added)
    return changed * 2 > (len(old) + len(new))
