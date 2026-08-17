"""Deterministic max+1 id allocation from existing records (no counter files)."""

from __future__ import annotations

import re
from typing import Iterable

WIDTHS = {"N": 4, "SYN": 4, "EV": 6, "DOC": 4}


def next_id(prefix: str, existing: Iterable[str]) -> str:
    width = WIDTHS[prefix]
    pat = re.compile(rf"^{prefix}-(\d+)$")
    top = 0
    for eid in existing:
        m = pat.match(eid)
        if m:
            top = max(top, int(m.group(1)))
    return f"{prefix}-{top + 1:0{width}d}"
