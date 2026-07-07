"""Request-level cache (docs/04 §Memoized Search #1).

Before dispatching any DocsWorker, the docs engine checks:
  a) fingerprint equality with any previously FULFILLED request  => cache hit
  b) the evidence matcher finds >=1 EvidenceUnit for the request's target claim
                                                                  => cache hit
A cache hit resolves the request as status=fulfilled, fulfilled_by="cache" and
creates NO docs work item. A real miss becomes status=open + a docs_queue item.
"""

from __future__ import annotations

from typing import Any

from ..paths import Paths
from ..store import jsonl
from . import matcher

DOCS_REQUESTS = "docs/docs_requests.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"


def fingerprint_hit(paths: Paths, fp: str) -> bool:
    """(a) fingerprint equality with any previously fulfilled request."""
    for r in jsonl.latest_records(paths.resolve(DOCS_REQUESTS), "request_id"):
        if r.get("status") == "fulfilled" and r.get("fingerprint") == fp:
            return True
    return False


def matcher_hit(paths: Paths, target_record: dict[str, Any]) -> bool:
    """(b) the evidence matcher finds >=1 EvidenceUnit for the target claim."""
    if target_record is None:
        return False
    if "edge_id" in target_record:
        claim, scope = target_record.get("edge_claim", "") or "", {}
    else:
        claim, scope = target_record.get("claim", "") or "", target_record.get("scope", {}) or {}
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    return bool(matcher.match(claim, scope, eus))


def is_cache_hit(paths: Paths, fp: str, target_record: dict[str, Any]) -> bool:
    """Cache hit iff a fingerprint match OR a matcher hit for the target claim."""
    return fingerprint_hit(paths, fp) or matcher_hit(paths, target_record)
