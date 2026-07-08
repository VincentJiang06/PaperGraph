"""Injectable clock + actor identity (NODIFY_NOW / NODIFY_ACTOR)."""

from __future__ import annotations

import os
from datetime import datetime, timezone


def now() -> str:
    override = os.environ.get("NODIFY_NOW")
    if override:
        return override
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def actor(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    return os.environ.get("NODIFY_ACTOR", "main")
