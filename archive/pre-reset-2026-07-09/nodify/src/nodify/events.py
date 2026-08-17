"""The trace log (anti-failure: retrofitting tracing is impossible — it ships
in V1). Every nd command, read-only included, appends exactly one event."""

from __future__ import annotations

from . import store
from .clock import actor as clock_actor
from .clock import now as clock_now
from .ids import next_id
from .paths import EVENTS, Paths
from .schemas import validate


def log(paths: Paths, command: str, *, mutating: bool,
        touched: list[str] | None = None, summary: str) -> dict:
    path = paths.resolve(EVENTS)
    event = {
        "schema": "event.v1",
        "event_id": next_id("EV", [e["event_id"] for e in store.read_all(path)]),
        "at": clock_now(),
        "actor": clock_actor(),
        "command": command,
        "mutating": mutating,
        "touched": list(touched or []),
        "summary": summary[:300],
    }
    errs = validate(event)
    if errs:  # a broken event record is a bug in nd itself — never write it
        raise AssertionError(f"internal: invalid event record: {errs}")
    store.append(path, event)
    return event


def read(paths: Paths, tail: int | None = None) -> list[dict]:
    events = store.read_all(paths.resolve(EVENTS))
    return events[-tail:] if tail else events
