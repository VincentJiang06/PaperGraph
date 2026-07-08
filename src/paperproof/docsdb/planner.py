"""The deterministic SearchPlan compiler (docs/14 §"The plan compiler").

NO LLM. Given a DocsRequest ``need`` + ``search_hints`` and the target/contract
scope, it produces a byte-identical ``search_plan.v1`` — the golden-testable
floor the DocsWorker must execute (docs/14). The ONLY tokenizer is
``textutil.tokens`` (docs/09 §0, CJK-aware).

Operationalization (S1 build — pinned in docs/14 "Operationalization"):
  * "≤6 highest-frequency non-stopword tokens ... minus scope tokens" is read as:
    drop stopwords AND scope tokens FIRST, then rank remaining tokens by
    (frequency desc, first-occurrence asc) and take the first six.
  * "strongest hint token" (narrow query) := over tokens() of all search_hints,
    excluding stopwords, scope tokens, and any token already in core_terms[:3],
    the highest-frequency one (ties → first occurrence); absent ⇒ narrow query is
    just core_terms[:3].
  * period is kept verbatim; only the region is casefolded.
  * scope fallback: the target scope is used when it carries a period or region,
    otherwise the contract scope.
  * a DocsRequest carries no angle (docs_request.v1 has none); ``docs plan`` and
    the dispatch path default angle=official_stats.
  * stop thresholds are the fixed floor {max_queries:8, min_docs:2, min_eus:4}.
The formula block (docs/14) is authoritative; the doc's illustrative JSON example
does not strictly follow it (Q2/Q3/Q4 are hand-abbreviated).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from ..errors import DomainError
from ..paths import Paths
from ..schemas.search import SearchPlan
from ..store import jsonl
from ..textutil import STOPWORDS, casefold, tokens

# docs/14 ANGLE_SUFFIX table (exact).
ANGLE_SUFFIX: dict[str, str] = {
    "official_stats": "official statistics",
    "academic": "study peer-reviewed",
    "industry": "industry report data",
    "counter": "evidence against",
    "news": "news report",
}

# docs/14: the frozen counter list; the counter query uses the first two.
COUNTER_TERMS: list[str] = ["decline", "criticism", "contrary", "evidence against", "refute"]

DEFAULT_STOP: dict[str, int] = {"max_queries": 8, "min_docs": 2, "min_eus": 4}
DEFAULT_ANGLE = "official_stats"

PLANS_DIR = "docs/plans"
DOCS_REQUESTS = "docs/docs_requests.jsonl"
CONTRACT = "specs/project_contract.json"


# --- pure compiler ----------------------------------------------------------


def _ranked_unique(toks: list[str]) -> list[str]:
    """Tokens ranked by (frequency desc, first-occurrence asc), deduplicated."""
    freq = Counter(toks)
    first_idx: dict[str, int] = {}
    for i, t in enumerate(toks):
        first_idx.setdefault(t, i)
    return sorted(freq.keys(), key=lambda t: (-freq[t], first_idx[t]))


def _scope_terms(target_scope: dict[str, Any], contract_scope: dict[str, Any]) -> list[str]:
    src = target_scope if (target_scope.get("period") or target_scope.get("region")) else contract_scope
    terms: list[str] = []
    period = src.get("period")
    if period:
        terms.append(str(period))
    region = src.get("region")
    if region:
        terms.append(casefold(str(region)))
    return terms


def _core_terms(need: str, scope_token_set: set[str]) -> list[str]:
    toks = [t for t in tokens(need) if t not in STOPWORDS and t not in scope_token_set]
    return _ranked_unique(toks)[:6]


def _strongest_hint_token(search_hints: list[str], scope_token_set: set[str], exclude: set[str]) -> str | None:
    hint_toks: list[str] = []
    for h in search_hints:
        hint_toks += tokens(h)
    cand = [t for t in hint_toks if t not in STOPWORDS and t not in scope_token_set and t not in exclude]
    ranked = _ranked_unique(cand)
    return ranked[0] if ranked else None


def _join(*parts: str) -> str:
    return " ".join(p for p in parts if p).strip()


def compile_plan(
    request_id: str,
    project_id: str,
    angle: str,
    need: str,
    search_hints: list[str],
    target_scope: dict[str, Any] | None,
    contract_scope: dict[str, Any] | None,
) -> SearchPlan:
    """Compile a byte-identical ``search_plan.v1`` (docs/14). Deterministic."""
    if angle not in ANGLE_SUFFIX:
        raise DomainError([f"unknown angle {angle!r}; must be one of {sorted(ANGLE_SUFFIX)}"])
    target_scope = target_scope or {}
    contract_scope = contract_scope or {}
    search_hints = list(search_hints or [])

    scope_terms = _scope_terms(target_scope, contract_scope)
    scope_token_set = set(tokens(" ".join(scope_terms)))
    core_terms = _core_terms(need, scope_token_set)
    counter_terms = list(COUNTER_TERMS)

    q1 = _join(" ".join(core_terms), " ".join(scope_terms))
    q2 = _join(q1, ANGLE_SUFFIX[angle])
    narrow_head = core_terms[:3]
    strongest = _strongest_hint_token(search_hints, scope_token_set, set(narrow_head))
    narrow = _join(" ".join(narrow_head), strongest or "")
    counter = _join(q1, counter_terms[0], counter_terms[1])

    ordered: list[tuple[str, str]] = [("core", q1), ("angle", q2)]
    for h in search_hints:
        ordered.append(("hint", h.strip()))
    ordered.append(("narrow", narrow))
    ordered.append(("counter", counter))

    # dedup by exact text (first occurrence wins), drop empties.
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for kind, text in ordered:
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append((kind, text))

    # cap at max_queries but keep the MANDATORY counter query (docs/14).
    max_q = DEFAULT_STOP["max_queries"]
    if len(deduped) > max_q:
        counter_item = next((x for x in deduped if x[0] == "counter"), None)
        deduped = deduped[:max_q]
        if counter_item is not None and counter_item not in deduped:
            deduped[-1] = counter_item
    if not any(kind == "counter" for kind, _ in deduped):
        # the counter query is mandatory in every plan, regardless of angle.
        if deduped:
            deduped[-1] = ("counter", counter)
        else:
            deduped.append(("counter", counter))

    queries = [{"qid": f"Q{i}", "kind": kind, "text": text} for i, (kind, text) in enumerate(deduped, start=1)]

    return SearchPlan.model_validate(
        {
            "schema_version": "search_plan.v1",
            "plan_id": f"SP-{request_id}",
            "request_id": request_id,
            "project_id": project_id,
            "angle": angle,
            "facets": {
                "core_terms": core_terms,
                "scope_terms": scope_terms,
                "counter_terms": counter_terms,
            },
            "queries": queries,
            "stop": dict(DEFAULT_STOP),
        }
    )


# --- storage + dispatch attach ---------------------------------------------


def plan_relpath(request_id: str) -> str:
    return f"{PLANS_DIR}/SP-{request_id}.json"


def plan_path(paths: Paths, request_id: str) -> Path:
    return paths.resolve(plan_relpath(request_id))


def load_plan(paths: Paths, request_id: str) -> dict[str, Any] | None:
    p = plan_path(paths, request_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _contract_scope(paths: Paths) -> dict[str, Any]:
    cp = paths.resolve(CONTRACT)
    if not cp.exists():
        return {}
    return json.loads(cp.read_text(encoding="utf-8")).get("scope") or {}


def plan_for_request(paths: Paths, request_id: str, angle: str = DEFAULT_ANGLE) -> dict[str, Any]:
    """Compile (once) or reprint the immutable plan for a request. Plans are
    bundle-grade artifacts: written once, then reprinted byte-for-byte."""
    p = plan_path(paths, request_id)
    if not p.exists():
        req = jsonl.latest_by_id(paths.resolve(DOCS_REQUESTS), "request_id").get(request_id)
        if req is None:
            raise DomainError([f"docs request not found: {request_id}"])
        from ..graph import model as graph_model  # local: avoid import cycle

        rec = graph_model.load(paths).record(req.get("target_id"))
        target_scope = (rec.get("scope") or {}) if (rec and "node_id" in rec) else {}
        plan = compile_plan(
            request_id, paths.project_id, angle,
            req.get("need", ""), req.get("search_hints", []) or [],
            target_scope, _contract_scope(paths),
        )
        jsonl.write_json(p, plan)
    return json.loads(p.read_text(encoding="utf-8"))
