"""Canonical serialization (docs/07).

UTF-8, compact separators, no ASCII-escaping, schema field order, one record per
line, trailing newline. Same data => same bytes. Everything that writes canonical
state goes through here; nobody hand-rolls JSON writing.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


def to_canonical_obj(obj: Any) -> Any:
    """Return the JSON-ready object (dict/list/scalar) in schema field order.

    Pydantic ``model_dump(mode="json")`` preserves field definition order, and
    Python dicts preserve insertion order, so the resulting bytes are stable.
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    return obj


def canonical_line(obj: Any) -> str:
    """One canonical JSON line (no trailing newline)."""
    data = to_canonical_obj(obj)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def canonical_bytes(obj: Any) -> bytes:
    """One canonical record: a single JSON line plus a trailing newline."""
    return (canonical_line(obj) + "\n").encode("utf-8")
