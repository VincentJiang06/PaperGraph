"""Session init/load. session.v1 stays deliberately tiny (anti-failure P15)."""

from __future__ import annotations

from typing import Any

from . import store
from .clock import now as clock_now
from .errors import DomainError, UsageError
from .paths import NODES, NOTES, SESSION, SYNTHESES, EVENTS, Paths
from .schemas import CURRENT_SET, schema_set_hash, set_name_of, validate

DEFAULT_BUDGETS = {"max_depth": 4, "max_children": 5, "max_open_claims": 12}


def init(paths: Paths, question: str, *, boundary_note: str | None = None,
         language: str = "zh", budgets: dict[str, int] | None = None) -> dict[str, Any]:
    if paths.exists():
        raise DomainError([f"session already exists: {paths.session_dir}"])
    merged = dict(DEFAULT_BUDGETS)
    for k, v in (budgets or {}).items():
        if k not in DEFAULT_BUDGETS:
            raise UsageError([f"unknown budget key: {k} (known: {sorted(DEFAULT_BUDGETS)})"])
        merged[k] = int(v)
    record = {
        "schema": "session.v1",
        "session_id": paths.session_id,
        "question": question,
        "boundary_note": boundary_note,
        "language": language,
        "budgets": merged,
        "schema_set_hash": schema_set_hash(),
        "created_at": clock_now(),
    }
    errs = validate(record)
    if errs:
        raise UsageError(errs)
    store.write_json(paths.resolve(SESSION), record)
    for rel in (NODES, SYNTHESES, EVENTS):
        p = paths.resolve(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()
    paths.resolve(NOTES).mkdir(parents=True, exist_ok=True)
    return record


def load(paths: Paths) -> dict[str, Any]:
    if not paths.exists():
        raise DomainError([f"no session at {paths.session_dir} (run nd init)"])
    record = store.read_json(paths.resolve(SESSION))
    errs = validate(record)
    if errs:
        raise DomainError([f"session.json is invalid: {e}" for e in errs])
    if set_name_of(record["schema_set_hash"]) is None:
        raise DomainError(
            ["schema set drift: this session's schema_set_hash matches no known "
             "frozen set (P5). Migrate explicitly; nd will not guess."])
    return record


def set_name(session: dict[str, Any]) -> str:
    name = set_name_of(session["schema_set_hash"])
    assert name is not None  # load() already refused unknown sets
    return name


def require_set(session: dict[str, Any], minimum: str) -> None:
    order = ["v1", "v2", "v3"]
    if order.index(set_name(session)) < order.index(minimum):
        raise DomainError(
            [f"this capability needs schema set {minimum}; the session is on "
             f"{set_name(session)} — run `nd upgrade` first"])


def upgrade(paths: Paths) -> dict[str, Any]:
    record = load(paths)
    before = set_name(record)
    if before == CURRENT_SET:
        return record  # idempotent
    record = {**record, "schema_set_hash": schema_set_hash(CURRENT_SET)}
    errs = validate(record)
    if errs:
        raise DomainError(errs)
    store.write_json(paths.resolve(SESSION), record)
    return record
