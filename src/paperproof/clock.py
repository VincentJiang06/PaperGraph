"""Injectable clock and actor identity (docs/07).

Timestamps are RFC 3339 UTC. The clock is injectable via PAPERPROOF_NOW so the
test harness can pin it. Actor identity reads PAPERPROOF_ACTOR (or the caller's
--agent flag, applied at the CLI layer).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone


def now() -> str:
    """RFC 3339 UTC timestamp. Reads PAPERPROOF_NOW verbatim if set."""
    pinned = os.environ.get("PAPERPROOF_NOW")
    if pinned:
        return pinned
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def actor(explicit: str | None = None) -> str:
    """--agent flag where present, else PAPERPROOF_ACTOR, else 'orchestrator'."""
    if explicit:
        return explicit
    return os.environ.get("PAPERPROOF_ACTOR") or "orchestrator"
