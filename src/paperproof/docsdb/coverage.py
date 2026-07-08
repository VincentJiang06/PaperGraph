"""Coverage ledger + saturation + role-profile floors (S4 — docs/17, docs/16 V-SRC-04).

This module SUPERSEDES the r3/m5 flat ">=2 EU / >=2 docs" floor and the r3 docs
round-trip cap. It computes, per non-rejected fact/mechanism node (and per bridge),
a DERIVED coverage ledger — a deterministic fold over existing canonical records
(graph bindings, evidence units, documents, the source registry, docs requests,
search waves) plus the persistent per-round critic coverage reports and S1
query_logs. There is NO new canonical writer: the ledger is rebuildable from state.

The ledger drives three decisions that used to be counts:
  * the role-profile FLOORS (spine_fact/mechanism, bridge, non-spine) that MSA-4,
    V-FRZ-02 and the compiler's missing_evidence gap all delegate to [V-COV-04];
  * TRIANGULATION of a spine binding profile (V-SRC-04);
  * SATURATION — the loop-until-dry stop criterion the committer consults instead
    of a request/verdict count [V-COV-03].

Everything here is pure given its inputs; ``build_context`` is the only reader.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from ..paths import Paths
from ..store import jsonl
from . import registry as _registry

EVIDENCE_UNITS = "docs/evidence_units.jsonl"
DOCUMENTS = "docs/documents.jsonl"
DOCS_REQUESTS = "docs/docs_requests.jsonl"
SOURCES = "docs/sources.jsonl"
WAVES = "docs/waves.jsonl"
COVERAGE_DIR = "agent_outputs/coverage_reports"
SINGLE_RESULT_DIR = "agent_outputs/docs_results"

# --- tiers -----------------------------------------------------------------

T1, T2, T3, T4, T5, T6 = (
    "T1_official", "T2_peer_reviewed", "T3_working_paper",
    "T4_industry_data", "T5_press", "T6_other",
)
_T1T2 = {T1, T2}
_T3T4 = {T3, T4}

# The ledger's per-angle outcome enum (docs/17). The critic's coverage form uses
# "yes" for a productive angle; the ledger renames it to "productive".
NO_ATTEMPT, TRIED_BLOCKED, TRIED_EMPTY, PRODUCTIVE = (
    "no_attempt", "tried_blocked", "tried_empty", "productive",
)
# Best-outcome ranking. tried_blocked ranks above tried_empty so a critic's
# explicit "blocked" verdict wins over a merely-attempted (member-inferred) angle;
# both are "attempted" (!= no_attempt) for saturation. productive always wins.
_ANGLE_RANK = {NO_ATTEMPT: 0, TRIED_EMPTY: 1, TRIED_BLOCKED: 2, PRODUCTIVE: 3}
_CRITIC_TO_LEDGER = {
    "yes": PRODUCTIVE, "tried_empty": TRIED_EMPTY,
    "tried_blocked": TRIED_BLOCKED, "no_attempt": NO_ATTEMPT,
}

# The always-mandatory saturation angles; industry joins for empirical market/firm
# claims (docs/17). news is displayed only when the claim's scope pulls it in.
BASE_MANDATORY = ("official_stats", "academic", "counter")
DISPLAY_ANGLES = ("official_stats", "academic", "industry", "counter")
_MARKET_TERMS = re.compile(
    r"\b(market|firm|firms|compan|employ|payroll|jobs?|wage|hir|industr|sector|"
    r"adoption|revenue|earnings|labou?r|workforce|productivity)\b",
    re.IGNORECASE,
)

_DRES_RE = re.compile(r"DRES-0*(\d+)")


def _dres_num(dres: str) -> int:
    m = _DRES_RE.search(dres or "")
    return int(m.group(1)) if m else -1


def _best(current: str, candidate: str) -> str:
    return candidate if _ANGLE_RANK[candidate] > _ANGLE_RANK[current] else current


# --- context (the single reader) -------------------------------------------


@dataclass
class CoverageContext:
    spine_ids: set[str]
    eus_by_id: dict[str, dict[str, Any]]
    docs_by_id: dict[str, dict[str, Any]]
    sources_by_domain: dict[str, dict[str, Any]]
    requests_latest: list[dict[str, Any]]       # latest per request_id
    wave_by_request: dict[str, dict[str, Any]]   # latest wave per request_id
    coverage_reports_by_wave: dict[str, list[dict[str, Any]]]
    single_query_logs: dict[str, list[dict[str, Any]]]  # request_id -> query_log
    docs_by_dres: dict[str, list[str]] = field(default_factory=dict)


def build_context(paths: Paths, spine_ids: set[str]) -> CoverageContext:
    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    docs = jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")
    sources = jsonl.latest_records(paths.resolve(SOURCES), "domain")
    requests = jsonl.latest_records(paths.resolve(DOCS_REQUESTS), "request_id")
    waves = jsonl.latest_records(paths.resolve(WAVES), "wave_id")

    eus_by_id = {e["evidence_id"]: e for e in eus}
    docs_by_id = {d["doc_id"]: d for d in docs}
    sources_by_domain = {s["domain"]: s for s in sources}

    wave_by_request: dict[str, dict[str, Any]] = {}
    for w in waves:
        wave_by_request[w.get("request_id")] = w

    docs_by_dres: dict[str, list[str]] = {}
    for d in docs:
        src = d.get("ingested_from")
        if isinstance(src, str) and src.startswith("DRES-"):
            docs_by_dres.setdefault(src, []).append(d["doc_id"])

    # persistent per-round critic coverage reports (agent_outputs, keyed by wave).
    coverage_reports_by_wave: dict[str, list[dict[str, Any]]] = {}
    cov_dir = paths.resolve(COVERAGE_DIR)
    if cov_dir.exists():
        for p in sorted(cov_dir.glob("*.coverage_report.json")):
            try:
                rep = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            wid = rep.get("wave_id") or p.name.split(".", 1)[0]
            coverage_reports_by_wave.setdefault(wid, []).append(rep)

    # S1 query_logs for single (non-wave) requests (agent_outputs).
    single_query_logs: dict[str, list[dict[str, Any]]] = {}
    sdir = paths.resolve(SINGLE_RESULT_DIR)
    if sdir.exists():
        for r in requests:
            rid = r.get("request_id")
            if rid in wave_by_request:
                continue
            f = sdir / f"{rid}.docs_result.json"
            if not f.exists():
                continue
            try:
                res = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            ql = res.get("query_log")
            if isinstance(ql, list) and ql:
                single_query_logs[rid] = ql

    return CoverageContext(
        spine_ids=set(spine_ids), eus_by_id=eus_by_id, docs_by_id=docs_by_id,
        sources_by_domain=sources_by_domain, requests_latest=requests,
        wave_by_request=wave_by_request,
        coverage_reports_by_wave=coverage_reports_by_wave,
        single_query_logs=single_query_logs, docs_by_dres=docs_by_dres,
    )


# --- publisher / tier resolution -------------------------------------------


def _doc_domain(doc: dict[str, Any]) -> Optional[str]:
    return _registry.domain_from_url(((doc.get("origin") or {}).get("url")))


def _doc_tier(doc: dict[str, Any]) -> str:
    prov = doc.get("provenance") or {}
    return prov.get("tier") or _registry.tier_for(doc.get("source_type", ""))


def _publisher_of(doc: dict[str, Any], sources_by_domain: dict[str, dict[str, Any]]) -> str:
    """Mechanical publisher identity for triangulation independence (docs/16): the
    registry publisher for the doc's domain if known, else the domain itself, else
    the doc id (a local file is its own publisher)."""
    domain = _doc_domain(doc)
    if domain:
        prof = sources_by_domain.get(domain)
        pub = (prof or {}).get("publisher") or ""
        return pub.strip().lower() if pub.strip() else domain
    return f"local:{doc.get('doc_id')}"


# --- triangulation (V-SRC-04) ----------------------------------------------


def triangulated(binding_docmeta: list[tuple[str, str, str]]) -> bool:
    """A spine binding profile satisfies triangulation (docs/16 V-SRC-04) iff:
      (a) >=1 EU from a T1/T2 document PLUS >=1 more EU from a DISTINCT document, or
      (b) >=2 EUs from distinct, mutually-independent T3/T4 documents (different
          publishers — publisher equality is the mechanical check).
    ``binding_docmeta`` = (tier, publisher, doc_id) per binding EU. T5 press never
    carries a spine binding alone (it fails both branches)."""
    distinct_docs = {doc_id for _t, _p, doc_id in binding_docmeta}
    # (a): a T1/T2-anchored profile with >=2 distinct documents.
    has_t1t2 = any(tier in _T1T2 for tier, _p, _d in binding_docmeta)
    if has_t1t2 and len(distinct_docs) >= 2:
        return True
    # (b): >=2 distinct T3/T4 documents from >=2 distinct publishers.
    t34_pub_by_doc: dict[str, str] = {}
    for tier, pub, doc_id in binding_docmeta:
        if tier in _T3T4:
            t34_pub_by_doc[doc_id] = pub
    if len(t34_pub_by_doc) >= 2 and len(set(t34_pub_by_doc.values())) >= 2:
        return True
    return False


# --- role classification + floors (docs/17 table) --------------------------


def classify_role(node: dict[str, Any], spine_ids: set[str]) -> str:
    """The role whose floor a node must clear: spine_fact | spine_mechanism |
    bridge | nonspine | none (docs/17). Only fact/mechanism nodes carry a floor;
    a bridge (origin.kind=bridge) that repairs a spine edge carries the strictest
    one. definition/question/thesis/alternative => none."""
    nt = node.get("node_type")
    if nt not in ("fact", "mechanism"):
        return "none"
    if (node.get("origin") or {}).get("kind") == "bridge":
        return "bridge"
    if node.get("node_id") in spine_ids:
        return "spine_fact" if nt == "fact" else "spine_mechanism"
    return "nonspine"


def _mandatory_angles(node: dict[str, Any]) -> tuple[str, ...]:
    """The saturation-mandatory angles for a node: official_stats/academic/counter
    always; industry too for an empirical claim whose scope names market/firm
    actors (docs/17)."""
    angles = list(BASE_MANDATORY)
    scope = node.get("scope") or {}
    blob = " ".join(
        [str(node.get("claim", ""))]
        + [str(scope.get(k) or "") for k in ("period", "region")]
        + [" ".join(scope.get("actors") or [])]
        + [" ".join(scope.get("mechanisms") or [])]
    )
    if _MARKET_TERMS.search(blob):
        angles.append("industry")
    return tuple(angles)


# --- the fold: one node's ledger -------------------------------------------


def _binding_eus(node: dict[str, Any], ctx: CoverageContext) -> list[dict[str, Any]]:
    return [ctx.eus_by_id[b] for b in (node.get("evidence_bindings") or []) if b in ctx.eus_by_id]


def _angle_outcomes(
    target_id: str, node: Optional[dict[str, Any]], ctx: CoverageContext,
    binding_eus: list[dict[str, Any]],
) -> dict[str, str]:
    """Fold per-angle outcomes from S2 wave rounds (member angles + the critic's
    per-round coverage reports), S1 query_logs (single requests), and the evidence
    the searches actually produced (tier -> angle, refutes -> counter). Best
    outcome wins."""
    angles = {a: NO_ATTEMPT for a in DISPLAY_ANGLES}
    if node is not None and "industry" not in _mandatory_angles(node):
        # industry stays displayed but is not mandatory unless market/firm.
        pass

    reqs = [r for r in ctx.requests_latest if r.get("target_id") == target_id]
    completed = [r for r in reqs if r.get("status") in ("fulfilled", "not_found")]

    # 1. any completed search round attempts the mandatory counter query (V-SP-02:
    #    the plan's counter query is executed or blocked, never skipped) and, for a
    #    single default-angle request, the official_stats angle.
    for r in completed:
        angles["counter"] = _best(angles["counter"], TRIED_EMPTY)
        if r.get("request_id") not in ctx.wave_by_request:
            angles["official_stats"] = _best(angles["official_stats"], TRIED_EMPTY)

    # 2. wave members: every fanned angle was attempted this wave.
    for r in reqs:
        wave = ctx.wave_by_request.get(r.get("request_id"))
        if wave is None:
            continue
        for mem in wave.get("members", []):
            a = mem.get("angle")
            if a in angles:
                angles[a] = _best(angles[a], TRIED_EMPTY)

    # 3. evidence the searches produced (bindings): tier -> productive angle.
    for eu in binding_eus:
        doc = ctx.docs_by_id.get(eu.get("doc_id"))
        if doc is not None:
            tier = _doc_tier(doc)
            if tier == T1:
                angles["official_stats"] = _best(angles["official_stats"], PRODUCTIVE)
            elif tier in (T2, T3):
                angles["academic"] = _best(angles["academic"], PRODUCTIVE)
            elif tier == T4:
                angles["industry"] = _best(angles["industry"], PRODUCTIVE)
        if eu.get("support_direction") == "refutes":
            angles["counter"] = _best(angles["counter"], PRODUCTIVE)

    # 4. S1 query_logs for single requests: overall productivity -> the request's
    #    default angle + the counter query.
    for r in reqs:
        rid = r.get("request_id")
        ql = ctx.single_query_logs.get(rid)
        if not ql:
            continue
        outcomes = {e.get("outcome") for e in ql}
        if "productive" in outcomes:
            angles["official_stats"] = _best(angles["official_stats"], PRODUCTIVE)
        elif outcomes == {"blocked"}:
            angles["official_stats"] = _best(angles["official_stats"], TRIED_BLOCKED)

    # 5. S2 critic coverage reports: the authoritative per-angle verdict.
    for r in reqs:
        wave = ctx.wave_by_request.get(r.get("request_id"))
        if wave is None:
            continue
        for rep in ctx.coverage_reports_by_wave.get(wave.get("wave_id"), []):
            ac = (rep.get("form") or {}).get("angle_covered") or {}
            for a in angles:
                mapped = _CRITIC_TO_LEDGER.get(ac.get(a))
                if mapped is not None:
                    angles[a] = _best(angles[a], mapped)

    return angles


def _rounds_and_new_docs(target_id: str, ctx: CoverageContext) -> tuple[int, int]:
    """rounds = completed search rounds for the node (each closed wave contributes
    its round count; each completed single request contributes 1). new_docs_last_
    round = distinct NEW documents first-archived by the most recent DRES."""
    reqs = [r for r in ctx.requests_latest if r.get("target_id") == target_id]
    rounds = 0
    counted_wave_reqs: set[str] = set()
    dres_ids: set[str] = set()
    for r in reqs:
        rid = r.get("request_id")
        fb = r.get("fulfilled_by")
        if isinstance(fb, str) and fb.startswith("DRES-"):
            dres_ids.add(fb)
        wave = ctx.wave_by_request.get(rid)
        if wave is not None:
            if wave.get("status") == "closed" and rid not in counted_wave_reqs:
                rounds += int(wave.get("round", 1) or 1)
                counted_wave_reqs.add(rid)
        elif r.get("status") in ("fulfilled", "not_found"):
            rounds += 1
    if not dres_ids:
        return rounds, 0
    last_dres = max(dres_ids, key=_dres_num)
    new_docs_last_round = len(ctx.docs_by_dres.get(last_dres, []))
    return rounds, new_docs_last_round


def is_saturated(rounds: int, angles: dict[str, str], new_docs_last_round: int,
                 mandatory: tuple[str, ...]) -> bool:
    """The loop-until-dry stop criterion (docs/17): rounds>=2 AND every mandatory
    angle not no_attempt AND the last round produced no new documents."""
    if rounds < 2:
        return False
    if any(angles.get(a, NO_ATTEMPT) == NO_ATTEMPT for a in mandatory):
        return False
    return new_docs_last_round == 0


def target_ledger(target_record: dict[str, Any], ctx: CoverageContext) -> dict[str, Any]:
    """Compute the DERIVED coverage ledger for a node or edge target (docs/17)."""
    is_node = "node_id" in target_record
    target_id = target_record.get("node_id") or target_record.get("edge_id")
    node = target_record if is_node else None

    binding_eus = _binding_eus(node, ctx) if node is not None else []
    eu_counts = {"supports": 0, "refutes": 0, "context": 0}
    binding_docmeta: list[tuple[str, str, str]] = []
    docs_seen: set[str] = set()
    publishers: set[str] = set()
    tiers: set[str] = set()
    for eu in binding_eus:
        direction = eu.get("support_direction", "context")
        if direction in eu_counts:
            eu_counts[direction] += 1
        doc = ctx.docs_by_id.get(eu.get("doc_id"))
        if doc is not None:
            tier = _doc_tier(doc)
            pub = _publisher_of(doc, ctx.sources_by_domain)
            binding_docmeta.append((tier, pub, doc["doc_id"]))
            docs_seen.add(doc["doc_id"])
            publishers.add(pub)
            tiers.add(tier)

    angles = _angle_outcomes(target_id, node, ctx, binding_eus)
    rounds, new_docs_last_round = _rounds_and_new_docs(target_id, ctx)
    mandatory = _mandatory_angles(node) if node is not None else BASE_MANDATORY
    saturated = is_saturated(rounds, angles, new_docs_last_round, mandatory)

    role = classify_role(node, ctx.spine_ids) if node is not None else "none"
    binding_count = len(node.get("evidence_bindings") or []) if node is not None else 0
    distinct_docs = len(docs_seen)
    is_triangulated = triangulated(binding_docmeta)
    met = _role_floor_met(role, binding_count, distinct_docs, is_triangulated, angles)

    ledger: dict[str, Any] = {
        "node_id": target_id,
        "eu_counts": eu_counts,
        "distinct_docs": distinct_docs,
        "distinct_publishers": len(publishers),
        "tiers_present": sorted(tiers),
        "angles": angles,
        "rounds": rounds,
        "new_docs_last_round": new_docs_last_round,
        "saturated": saturated,
        "floor": {"required": role, "met": met},
        "triangulated": is_triangulated,
        "mandatory_angles": list(mandatory),
    }
    return ledger


def _role_floor_met(role: str, binding_count: int, distinct_docs: int,
                    is_triangulated: bool, angles: dict[str, str]) -> bool:
    """The role-profile floors (docs/17) — supersedes the flat >=2 rule."""
    if role == "none":
        return True
    if role == "nonspine":
        return binding_count >= 1
    counter_attempted = angles.get("counter", NO_ATTEMPT) != NO_ATTEMPT
    spine_ok = binding_count >= 2 and distinct_docs >= 2 and is_triangulated and counter_attempted
    if role in ("spine_fact", "spine_mechanism"):
        return spine_ok
    if role == "bridge":
        return spine_ok and distinct_docs >= 3
    return True  # pragma: no cover


def meets_floor(ledger: dict[str, Any]) -> bool:
    return bool(ledger["floor"]["met"])


def floor_line(ledger: dict[str, Any]) -> str:
    """One-line per-node ledger summary msa-check prints for every miss (docs/17)."""
    f = ledger["floor"]
    ec = ledger["eu_counts"]
    return (
        f"{ledger['node_id']} role={f['required']} met={f['met']} "
        f"EU(s={ec['supports']}/r={ec['refutes']}/c={ec['context']}) "
        f"docs={ledger['distinct_docs']} pubs={ledger['distinct_publishers']} "
        f"triangulated={ledger['triangulated']} "
        f"counter={ledger['angles'].get('counter')} "
        f"rounds={ledger['rounds']} new_last={ledger['new_docs_last_round']} "
        f"saturated={ledger['saturated']}"
    )


# --- whole-project ledger (docs coverage / /api/coverage) ------------------


def _is_ledger_target(node: dict[str, Any]) -> bool:
    if node.get("lifecycle_state") == "rejected":
        return False
    return node.get("node_type") in ("fact", "mechanism") or (
        (node.get("origin") or {}).get("kind") == "bridge"
    )


def build_ledger(paths: Paths) -> dict[str, Any]:
    """The whole-project coverage ledger: one line per non-rejected fact/mechanism
    node (and per bridge). DERIVED — a deterministic fold, no canonical write."""
    from ..graph import model as graph_model

    gv = graph_model.load(paths)
    spine_ids, _ = gv.spine()
    ctx = build_context(paths, spine_ids)
    ledgers = [
        target_ledger(n, ctx) for n in sorted(gv.nodes, key=lambda n: n["node_id"])
        if _is_ledger_target(n)
    ]
    return {"ledger": ledgers, "count": len(ledgers), "spine": sorted(spine_ids)}


def ledger_for(paths: Paths, node_id: str) -> dict[str, Any]:
    """The coverage ledger line for a single node (``docs coverage --node``)."""
    from ..graph import model as graph_model

    gv = graph_model.load(paths)
    rec = gv.node_by_id.get(node_id) or gv.edge_by_id.get(node_id)
    if rec is None:
        from ..errors import DomainError

        raise DomainError([f"record not found: {node_id}"])
    spine_ids, _ = gv.spine()
    ctx = build_context(paths, spine_ids)
    return {"ledger": target_ledger(rec, ctx)}
