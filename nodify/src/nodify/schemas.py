"""Runtime schema loading + validation. The schema FILES are the single source
of truth (anti-failure P9) — there is deliberately no second model layer.
"""

from __future__ import annotations

import hashlib
import json
from functools import cache
from importlib import resources
from typing import Any

import jsonschema

SCHEMA_NAMES = ("envelope.v1", "session.v1", "node.v1", "synthesis.v1", "event.v1")


@cache
def _schema_texts() -> dict[str, str]:
    pkg = resources.files("nodify") / "schemas"
    return {
        name: (pkg / f"{name}.schema.json").read_text(encoding="utf-8")
        for name in SCHEMA_NAMES
    }


@cache
def load(name: str) -> dict[str, Any]:
    return json.loads(_schema_texts()[name])


@cache
def _validator(name: str) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(load(name))


def validate(record: dict[str, Any]) -> list[str]:
    """Validate a record against the schema named in its `schema` field.
    Returns a list of human-readable errors; empty = valid."""
    name = record.get("schema")
    if name not in SCHEMA_NAMES:
        return [f"unknown or missing schema field: {name!r}"]
    errs = []
    for e in _validator(name).iter_errors(record):
        path = "$" + "".join(
            f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path
        )
        errs.append(f"{name} @ {path}: {e.message}")
    return sorted(errs)


def schema_set_hash() -> str:
    """sha256 over the frozen schema file bytes, in name order (P5: the
    session pins this at init; drift is detectable)."""
    h = hashlib.sha256()
    for name in SCHEMA_NAMES:
        h.update(name.encode())
        h.update(_schema_texts()[name].encode())
    return "sha256:" + h.hexdigest()
