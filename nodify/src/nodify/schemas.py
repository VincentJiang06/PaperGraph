"""Runtime schema loading + validation. The schema FILES are the single source
of truth (anti-failure P9) — there is deliberately no second model layer.

V2 introduces NAMED frozen sets (P5): a session pins the hash of the set it
was created under; nd recognizes every historical set and refuses capabilities
the session's set does not contain (`nd upgrade` is the only migration path).
"""

from __future__ import annotations

import hashlib
import json
from functools import cache
from importlib import resources
from typing import Any

import jsonschema

SCHEMA_NAMES = (
    "envelope.v1", "session.v1", "node.v1", "synthesis.v1", "event.v1",
    "docs.entry.v1", "recall.result.v1", "synthesis.v2",
)

# named frozen sets — order matters for the hash; never edit a released set
SETS: dict[str, tuple[str, ...]] = {
    "v1": ("envelope.v1", "session.v1", "node.v1", "synthesis.v1", "event.v1"),
    "v2": ("envelope.v1", "session.v1", "node.v1", "synthesis.v1", "event.v1",
            "synthesis.v2", "docs.entry.v1", "recall.result.v1"),
}
CURRENT_SET = "v2"


@cache
def _schema_texts() -> dict[str, str]:
    pkg = resources.files("nodify") / "schemas"
    return {name: (pkg / f"{name}.schema.json").read_text(encoding="utf-8")
            for name in SCHEMA_NAMES}


@cache
def load(name: str) -> dict[str, Any]:
    return json.loads(_schema_texts()[name])


@cache
def _validator(name: str) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(load(name))


def validate(record: dict[str, Any]) -> list[str]:
    """Validate a record against the schema named in its `schema` field."""
    name = record.get("schema")
    if name not in SCHEMA_NAMES:
        return [f"unknown or missing schema field: {name!r}"]
    errs = []
    for e in _validator(name).iter_errors(record):
        path = "$" + "".join(
            f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path)
        errs.append(f"{name} @ {path}: {e.message}")
    return sorted(errs)


@cache
def schema_set_hash(set_name: str = CURRENT_SET) -> str:
    h = hashlib.sha256()
    for name in SETS[set_name]:
        h.update(name.encode())
        h.update(_schema_texts()[name].encode())
    return "sha256:" + h.hexdigest()


def set_name_of(hash_value: str) -> str | None:
    for name in SETS:
        if schema_set_hash(name) == hash_value:
            return name
    return None
