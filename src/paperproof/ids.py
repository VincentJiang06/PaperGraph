"""ID formats and max+1 allocation (docs/07).

Ids are assigned only by code, by scanning the existing maximum per family (+1) -
no counter files, deterministic under the test harness. Widths are fixed;
counters grow past the width naturally.
"""

from __future__ import annotations

import re
from typing import Iterable

# Fixed zero-pad widths per family (docs/07 §ID formats).
WIDTHS: dict[str, int] = {
    "NODE": 3,
    "EDGE": 3,   # each numeric segment of an edge id
    "DOC": 3,
    "EU": 3,
    "DRES": 3,
    "PR": 3,
    "DR": 3,
    "TS": 3,
    "FRZ": 3,
    "CDR": 3,
    "AUD": 3,
    "DRAFTMAP": 3,
    "WI": 6,
    "QE": 6,
    "GS": 6,
    "CD": 6,
}

# Edge type -> id suffix (docs/07). supports is bare.
EDGE_TYPE_SUFFIX: dict[str, str] = {
    "supports": "",
    "depends_on": "-dep",
    "refutes": "-ref",
}


def _pad(prefix: str, n: int, width: int | None = None) -> str:
    w = width if width is not None else WIDTHS.get(prefix, 3)
    return f"{prefix}-{n:0{w}d}"


def _max_index(existing: Iterable[str], pattern: re.Pattern[str]) -> int:
    """Highest integer captured by ``pattern`` group 1 over ``existing``; 0 if none."""
    hi = 0
    for value in existing:
        m = pattern.match(value)
        if m:
            hi = max(hi, int(m.group(1)))
    return hi


def next_id(prefix: str, existing: Iterable[str], width: int | None = None) -> str:
    """Next simple counter id for a family: ``PREFIX-<max+1>`` zero-padded."""
    pat = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    return _pad(prefix, _max_index(existing, pat) + 1, width)


def node_id(existing_node_ids: Iterable[str]) -> str:
    """Next NODE-NNN id."""
    return next_id("NODE", existing_node_ids)


def _num(node_id_value: str) -> str:
    """Extract the zero-padded numeric segment of a NODE id (verbatim)."""
    m = re.match(r"^NODE-(\d+)$", node_id_value)
    if not m:
        raise ValueError(f"not a node id: {node_id_value!r}")
    return m.group(1)


def edge_id(
    source_node_id: str,
    target_node_id: str,
    edge_type: str,
    existing_edge_ids: Iterable[str],
) -> str:
    """Edge id ``EDGE-<src>-<tgt>[-dep|-ref][-vN]`` (docs/07, V-EDGE-03).

    ``supports`` is bare; ``depends_on`` appends ``-dep``; ``refutes`` appends
    ``-ref`` (so all three types can coexist between the same endpoints). A
    ``-vN`` marker is appended when the same (endpoints, type) recurs after a
    rejection.
    """
    if edge_type not in EDGE_TYPE_SUFFIX:
        raise ValueError(f"unknown edge_type: {edge_type!r}")
    base = f"EDGE-{_num(source_node_id)}-{_num(target_node_id)}{EDGE_TYPE_SUFFIX[edge_type]}"
    existing = set(existing_edge_ids)
    # version 1 == bare base; version N == base + '-vN'
    hi = 1 if base in existing else 0
    vpat = re.compile(rf"^{re.escape(base)}-v(\d+)$")
    for value in existing:
        m = vpat.match(value)
        if m:
            hi = max(hi, int(m.group(1)))
    if hi == 0:
        return base
    return f"{base}-v{hi + 1}"


# Bundle id kinds keyed by target id, with per-target -rN revisions.
_BUNDLE_PREFIXES = {"PT", "CTX", "DOCSPACK"}


def bundle_id(kind: str, target_id: str, revision: int = 1) -> str:
    """Proof-bundle id: ``<KIND>-<target_id>[-rN]`` (docs/03, docs/07).

    ``kind`` in {PT, CTX, DOCSPACK}; ``target_id`` is the full node/edge id
    (e.g. NODE-001, EDGE-001-002). Revision 1 is bare; N>=2 appends ``-rN``.
    """
    if kind not in _BUNDLE_PREFIXES:
        raise ValueError(f"unknown bundle kind: {kind!r}")
    if revision < 1:
        raise ValueError("revision must be >= 1")
    base = f"{kind}-{target_id}"
    return base if revision == 1 else f"{base}-r{revision}"


def next_bundle_revision(kind: str, target_id: str, existing_ids: Iterable[str]) -> int:
    """Next revision number for a target's bundle family (max existing + 1)."""
    base = re.escape(f"{kind}-{target_id}")
    bare = re.compile(rf"^{base}$")
    rpat = re.compile(rf"^{base}-r(\d+)$")
    hi = 0
    for value in existing_ids:
        if bare.match(value):
            hi = max(hi, 1)
        else:
            m = rpat.match(value)
            if m:
                hi = max(hi, int(m.group(1)))
    return hi + 1
