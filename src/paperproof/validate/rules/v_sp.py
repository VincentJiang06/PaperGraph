"""V-SP: search-plan accounting for a ``docs_result.v2`` (docs/14 §Rules).

The plan compiler emits an immutable ``search_plan.v1`` per DocsRequest; the
DocsWorker executes it and returns a ``query_log`` accounting for every planned
``qid``. V-SP rejects a result that leaves a plan line unaccounted, skips the
mandatory counter query, or reports impossible counts. These rules apply ONLY to
a v2 result (a v1 result carries a free-string ``search_log`` and is checked by
V-DR-06's v1 branch).

``check`` takes the raw result dict + the compiled plan dict (loaded from
``docs/plans/SP-<request>.json``); ``plan is None`` means no plan was compiled for
the referenced request ⇒ V-SP-05.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..envelope import Failure


def check(result_dict: dict[str, Any], plan: dict[str, Any] | None) -> list[Failure]:
    """V-SP-01..05. Applies only to ``docs_result.v2``."""
    if result_dict.get("schema_version") != "docs_result.v2":
        return []

    failures: list[Failure] = []
    request_id = result_dict.get("request_id")
    query_log = result_dict.get("query_log") or []
    documents = result_dict.get("documents") or []
    not_found = bool(result_dict.get("not_found"))

    # V-SP-05: the plan the result refers to exists and matches request_id.
    if plan is None:
        failures.append(Failure("V-SP-05", f"no compiled plan for request {request_id!r} (docs/plans/SP-{request_id}.json missing)"))
        return failures
    if plan.get("request_id") != request_id:
        failures.append(Failure("V-SP-05", f"plan request_id {plan.get('request_id')!r} != result request_id {request_id!r}"))

    plan_queries = plan.get("queries") or []
    plan_qids = [q.get("qid") for q in plan_queries]
    counter_qids = [q.get("qid") for q in plan_queries if q.get("kind") == "counter"]
    qid_counts = Counter(e.get("qid") for e in query_log)

    # V-SP-01: every plan qid appears exactly once; executed=false only with
    # outcome=blocked + a non-empty note.
    for qid in plan_qids:
        n = qid_counts.get(qid, 0)
        if n != 1:
            failures.append(Failure("V-SP-01", f"plan qid {qid!r} accounted {n} time(s) in query_log (want exactly 1)"))
    for e in query_log:
        if e.get("executed") is False:
            if e.get("outcome") != "blocked" or not str(e.get("note") or "").strip():
                failures.append(Failure("V-SP-01", f"query_log {e.get('qid')!r} executed=false requires outcome=blocked + a non-empty note"))

    # V-SP-02: the plan's counter query was executed or blocked — never skipped.
    for cq in counter_qids:
        entry = next((e for e in query_log if e.get("qid") == cq), None)
        if entry is None:
            failures.append(Failure("V-SP-02", f"counter query {cq!r} is absent from query_log (skipped)"))
        elif not (entry.get("executed") is True or entry.get("outcome") == "blocked"):
            failures.append(Failure("V-SP-02", f"counter query {cq!r} was skipped (not executed and not blocked)"))

    # V-SP-03: docs_taken <= urls_seen per entry; documents present ⇒ ≥1 productive.
    for e in query_log:
        dt = e.get("docs_taken") or 0
        us = e.get("urls_seen") or 0
        if dt > us:
            failures.append(Failure("V-SP-03", f"query_log {e.get('qid')!r} docs_taken {dt} > urls_seen {us}"))
    if documents and not any(e.get("outcome") == "productive" for e in query_log):
        failures.append(Failure("V-SP-03", f"{len(documents)} document(s) taken but no query_log entry is productive"))

    # V-SP-04: not_found ⇒ every entry executed|blocked and 0 productive.
    if not_found:
        for e in query_log:
            if not (e.get("executed") is True or e.get("outcome") == "blocked"):
                failures.append(Failure("V-SP-04", f"not_found=true but query_log {e.get('qid')!r} is neither executed nor blocked"))
        if any(e.get("outcome") == "productive" for e in query_log):
            failures.append(Failure("V-SP-04", "not_found=true but a query_log entry reports outcome=productive"))

    return failures
