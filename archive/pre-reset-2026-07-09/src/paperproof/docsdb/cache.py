"""Request-level cache (docs/04 §Memoized Search #1).

Before dispatching any DocsWorker, the docs engine checks fingerprint equality
with any previously FULFILLED request => cache hit. A cache hit resolves the
request as status=fulfilled, fulfilled_by="cache" and creates NO docs work item.
A real miss becomes status=open + a docs_queue item.

NOTE (r2.2, from the ai-jobs live run): the earlier "matcher finds >=1 EU for the
target claim => cache hit" trigger was REMOVED. The v1 matcher is a deliberately
dumb keyword matcher, so it produced FALSE cache hits — declaring a genuinely new
evidence need "fulfilled" merely because loosely-related evidence already existed,
silently overriding a ProofWorker's own "insufficient" judgment and blocking the
fresh search the argument required. Sufficiency is the ProofWorker's call (from
the matcher-populated DocsPack), not the cache's. The cache now only avoids
RE-RUNNING an identical search (fingerprint equality); the matcher still populates
DocsPacks exactly as before.
"""

from __future__ import annotations

from typing import Any

from ..paths import Paths
from ..store import jsonl

DOCS_REQUESTS = "docs/docs_requests.jsonl"


def fingerprint_hit(paths: Paths, fp: str) -> bool:
    """Fingerprint equality with a previously fulfilled request — but only one
    genuinely fulfilled by an ingest (fulfilled_by = a DRES id). Requests whose
    fulfilled_by is itself "cache" are never cache sources: a false hit must
    not chain (docs/04 r3; live-run DR-003..005 would otherwise satisfy every
    future identical search forever)."""
    for r in jsonl.latest_records(paths.resolve(DOCS_REQUESTS), "request_id"):
        if (
            r.get("status") == "fulfilled"
            and r.get("fingerprint") == fp
            and str(r.get("fulfilled_by") or "").startswith("DRES-")
        ):
            return True
    return False


def is_cache_hit(paths: Paths, fp: str, target_record: dict[str, Any]) -> bool:
    """Cache hit iff an identical (fingerprint-equal) request was already
    fulfilled. A matcher hit no longer short-circuits a fresh search — see the
    module docstring. `target_record` is retained for signature compatibility
    with the docs engine and is unused."""
    return fingerprint_hit(paths, fp)
