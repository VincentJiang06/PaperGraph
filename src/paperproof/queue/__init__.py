"""Queue engine package (docs/05): work items, leases, events, the 11-state
transition table, and the unblock/expire sweeps. The queue engine is the only
writer of queue/work_items.jsonl and queue/events.jsonl.
"""

from __future__ import annotations

from . import engine

__all__ = ["engine"]
