"""V-WAVE: the S2 search-orchestra rules (docs/15 §Rules).

```text
V-WAVE-01  member outputs are pairwise-distinct declared paths
V-WAVE-02  merger determinism: same terminal member set ⇒ byte-identical merged
           result; every merged doc/EU traces to exactly one member
V-WAVE-03  critic form is closed-enum complete; expected_sources ≤3 per round;
           the critic's output contains NO documents/evidence_units (read-only)
V-WAVE-04  rounds ≤ 2; every follow-up member cites its origin in the wave record
V-WAVE-05  only the merged result is ingested; exactly one DRES per wave
```

All checks are pure functions over dicts so both the runtime paths and the
tests call them directly.
"""

from __future__ import annotations

import hashlib
from typing import Any

from ..envelope import Failure

_ANGLE_VALS = {"yes", "tried_empty", "tried_blocked", "no_attempt"}
_PRESENCE_VALS = {"yes", "no", "n/a"}
R_MAX = 2


# --- V-WAVE-01 --------------------------------------------------------------


def check_member_paths(output_paths: list[str]) -> list[Failure]:
    """Every wave member declares a distinct output path."""
    seen: set[str] = set()
    dups: list[str] = []
    for p in output_paths:
        if p in seen and p not in dups:
            dups.append(p)
        seen.add(p)
    if dups:
        return [Failure("V-WAVE-01", f"wave member outputs are not pairwise distinct: {dups}")]
    return []


# --- V-WAVE-02 --------------------------------------------------------------


def _content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _norm(s: str) -> str:
    from ...textutil import normalize

    return normalize(s or "")


def check_merge(member_results: list[dict[str, Any]], merged: dict[str, Any],
                request_id: str, project_id: str) -> list[Failure]:
    """Merger determinism + traceability. Recomputes the merge and compares; then
    checks that every merged doc/EU traces to a member (docs/15)."""
    from ...docsdb import wave as wave_mod

    failures: list[Failure] = []
    recomputed = wave_mod.merge_results(request_id, project_id, member_results)
    if recomputed != merged:
        failures.append(Failure("V-WAVE-02", "merged result is not the deterministic merge of its members"))

    member_doc_hashes = {
        _content_hash(d.get("text") or "")
        for res in member_results for d in (res.get("documents") or [])
    }
    for d in merged.get("documents", []) or []:
        if _content_hash(d.get("text") or "") not in member_doc_hashes:
            failures.append(Failure("V-WAVE-02", f"merged document {d.get('citation_key')!r} traces to no member"))

    member_quotes = {
        _norm(eu.get("quote_or_paraphrase") or "")
        for res in member_results for eu in (res.get("evidence_units") or [])
    }
    for eu in merged.get("evidence_units", []) or []:
        if _norm(eu.get("quote_or_paraphrase") or "") not in member_quotes:
            failures.append(Failure("V-WAVE-02", f"merged evidence unit at {eu.get('location')!r} traces to no member"))
    return failures


# --- V-WAVE-03 --------------------------------------------------------------


def _scan_for_evidence_keys(obj: Any) -> bool:
    """True iff a ``documents`` or ``evidence_units`` key appears anywhere."""
    if isinstance(obj, dict):
        if "documents" in obj or "evidence_units" in obj:
            return True
        return any(_scan_for_evidence_keys(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_scan_for_evidence_keys(v) for v in obj)
    return False


def check_critic(raw: dict[str, Any], mandatory: tuple[str, ...]) -> list[Failure]:
    """V-WAVE-03. The critic is READ-ONLY: no documents/evidence_units; the form
    is closed-enum complete for every mandatory angle; expected_sources ≤3."""
    failures: list[Failure] = []
    if _scan_for_evidence_keys(raw):
        failures.append(Failure("V-WAVE-03", "critic output must contain no documents/evidence_units (read-only)"))

    form = raw.get("form")
    if not isinstance(form, dict):
        failures.append(Failure("V-WAVE-03", "coverage form is missing"))
        return failures
    ac = form.get("angle_covered")
    if not isinstance(ac, dict):
        failures.append(Failure("V-WAVE-03", "angle_covered is missing"))
    else:
        for a in mandatory:
            v = ac.get(a)
            if v not in _ANGLE_VALS:
                failures.append(Failure("V-WAVE-03", f"mandatory angle {a!r} not answered with a closed enum (got {v!r})"))
        for k, v in ac.items():
            if v is not None and v not in _ANGLE_VALS:
                failures.append(Failure("V-WAVE-03", f"angle {k!r} has out-of-enum value {v!r}"))
    if form.get("primary_source_present") not in _PRESENCE_VALS:
        failures.append(Failure("V-WAVE-03", f"primary_source_present out of enum: {form.get('primary_source_present')!r}"))
    if form.get("disconfirming_captured") not in _PRESENCE_VALS:
        failures.append(Failure("V-WAVE-03", f"disconfirming_captured out of enum: {form.get('disconfirming_captured')!r}"))

    es = raw.get("expected_sources") or []
    if len(es) > 3:
        failures.append(Failure("V-WAVE-03", f"expected_sources has {len(es)} entries (max 3 per round)"))
    return failures


# --- V-WAVE-04 --------------------------------------------------------------


def check_wave_rounds(wave: dict[str, Any], r_max: int = R_MAX) -> list[Failure]:
    """Rounds ≤ 2; every follow-up member (round>1) cites its origin."""
    failures: list[Failure] = []
    if wave.get("round", 1) > r_max:
        failures.append(Failure("V-WAVE-04", f"wave round {wave.get('round')} exceeds R_MAX={r_max}"))
    for mem in wave.get("members", []) or []:
        r = mem.get("round", 1)
        if r > r_max:
            failures.append(Failure("V-WAVE-04", f"member {mem.get('work_item_id')} round {r} exceeds R_MAX={r_max}"))
        if r > 1 and not str(mem.get("origin") or "").strip():
            failures.append(Failure("V-WAVE-04", f"follow-up member {mem.get('work_item_id')} (round {r}) cites no origin"))
    return failures


# --- V-WAVE-05 --------------------------------------------------------------


def check_single_dres(request_id: str, request_records: list[dict[str, Any]]) -> list[Failure]:
    """Exactly one DRES fulfils the wave's request (only the merged result was
    ingested). ``request_records`` is the full append history for the request."""
    failures: list[Failure] = []
    dres_ids = {
        r.get("fulfilled_by") for r in request_records
        if r.get("request_id") == request_id and str(r.get("fulfilled_by") or "").startswith("DRES-")
    }
    if len(dres_ids) > 1:
        failures.append(Failure("V-WAVE-05", f"request {request_id} was ingested by >1 DRES {sorted(dres_ids)} (per-member ingest?)"))
    latest = None
    for r in request_records:
        if r.get("request_id") == request_id:
            latest = r
    if latest is not None and latest.get("status") in ("fulfilled", "not_found"):
        if not str(latest.get("fulfilled_by") or "").startswith("DRES-"):
            failures.append(Failure("V-WAVE-05", f"request {request_id} terminal without a DRES fulfilment"))
    return failures
