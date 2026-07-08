"""Tree operations: add / promote / set-status / conclude.

No state-machine engine (anti-failure P4): a small LEGAL set for explicit
transitions, two auto-transitions (first child ⇒ parent expanding; conclude ⇒
synthesized/concluded), budgets checked at write time. All writes are appends;
latest record per id wins.
"""

from __future__ import annotations

from typing import Any

from . import store
from .clock import actor as clock_actor
from .clock import now as clock_now
from .errors import DomainError, UsageError
from .ids import next_id
from .paths import NODES, SYNTHESES, Paths
from .schemas import validate

# explicit transitions allowed through set_status (auto-transitions excluded)
LEGAL = {
    ("open", "expanding"), ("open", "retired"),
    ("expanding", "retired"),
    ("synthesized", "expanding"), ("synthesized", "closed"), ("synthesized", "retired"),
    ("pending", "investigating"), ("pending", "retired"), ("pending", "stuck"),
    ("investigating", "stuck"), ("investigating", "retired"),
    ("stuck", "investigating"), ("stuck", "retired"),
    ("concluded", "retired"),
    ("closed", "retired"),
}
NOTE_REQUIRED_STATUSES = {"retired", "stuck"}
CONCLUDABLE = {"open", "expanding", "synthesized",          # viewpoint
               "pending", "investigating", "concluded", "stuck"}  # claim
OPEN_CLAIM_STATUSES = {"pending", "investigating"}


def nodes_by_id(paths: Paths) -> dict[str, dict[str, Any]]:
    return store.latest_by_id(paths.resolve(NODES), "node_id")


def syntheses(paths: Paths) -> list[dict[str, Any]]:
    return store.read_all(paths.resolve(SYNTHESES))


def latest_synthesis(paths: Paths, node_id: str) -> dict[str, Any] | None:
    found = None
    for syn in syntheses(paths):
        if syn["node_id"] == node_id:
            found = syn
    return found


def depth_of(nodes: dict[str, dict], node_id: str) -> int:
    d = 0
    cur = nodes[node_id]
    while cur["parent_id"] is not None:
        cur = nodes[cur["parent_id"]]
        d += 1
    return d


def children_of(nodes: dict[str, dict], node_id: str) -> list[dict[str, Any]]:
    return sorted((n for n in nodes.values() if n["parent_id"] == node_id),
                  key=lambda n: n["node_id"])


def path_of(nodes: dict[str, dict], node_id: str) -> list[str]:
    chain = [node_id]
    cur = nodes[node_id]
    while cur["parent_id"] is not None:
        chain.append(cur["parent_id"])
        cur = nodes[cur["parent_id"]]
    return list(reversed(chain))


def _append_node(paths: Paths, record: dict[str, Any]) -> None:
    errs = validate(record)
    if errs:
        raise DomainError(errs)
    store.append(paths.resolve(NODES), record)


def _open_claims(nodes: dict[str, dict]) -> int:
    return sum(1 for n in nodes.values()
               if n["kind"] == "claim" and n["status"] in OPEN_CLAIM_STATUSES)


def add_children(paths: Paths, session: dict[str, Any], parent_id: str | None,
                 children: list[dict[str, Any]], *, actor: str | None = None,
                 ) -> list[dict[str, Any]]:
    """Add child nodes (or the root when parent_id is None). Each child spec:
    {statement, why_helps_parent?, orientation?, kind?, promotion_note?}."""
    nodes = nodes_by_id(paths)
    budgets = session["budgets"]
    actor = clock_actor(actor)

    if parent_id is None:
        if any(n["parent_id"] is None for n in nodes.values()):
            raise DomainError(["root already exists; pass --parent"])
        if len(children) != 1:
            raise UsageError(["the root add takes exactly one statement"])
    else:
        if parent_id not in nodes:
            raise DomainError([f"unknown parent: {parent_id}"])
        parent = nodes[parent_id]
        if parent["status"] in ("retired", "closed"):
            raise DomainError([f"parent {parent_id} is {parent['status']}"])
        if depth_of(nodes, parent_id) + 1 > budgets["max_depth"]:
            raise DomainError([f"budget max_depth={budgets['max_depth']} exceeded "
                               f"under {parent_id}"])
        room = budgets["max_children"] - len(children_of(nodes, parent_id))
        if len(children) > room:
            raise DomainError([f"budget max_children={budgets['max_children']} "
                               f"exceeded for {parent_id} (room: {room})"])

    made = []
    existing_ids = list(nodes)
    for spec in children:
        parent = nodes.get(parent_id) if parent_id else None
        kind = spec.get("kind") or ("claim" if parent and parent["kind"] == "claim"
                                    else "viewpoint")
        if parent is None and kind != "viewpoint":
            raise DomainError(["the root must be a viewpoint"])
        if parent and parent["kind"] == "viewpoint" and kind != "viewpoint":
            raise DomainError(["children of a viewpoint are viewpoints; promotion "
                               "re-kinds a node in place (nd promote)"])
        if parent and parent["kind"] == "claim" and kind != "claim":
            raise DomainError(["children of a claim are claims (拆解)"])
        promotion_note = spec.get("promotion_note")
        if kind == "claim" and not promotion_note:
            promotion_note = f"split from {parent_id}"
        if kind == "claim" and _open_claims(nodes) >= budgets["max_open_claims"]:
            raise DomainError([f"budget max_open_claims={budgets['max_open_claims']} reached"])
        node_id = next_id("N", existing_ids)
        existing_ids.append(node_id)
        record = {
            "schema": "node.v1",
            "node_id": node_id,
            "parent_id": parent_id,
            "kind": kind,
            "statement": spec["statement"],
            "why_helps_parent": spec.get("why_helps_parent"),
            "orientation": spec.get("orientation"),
            "status": "open" if kind == "viewpoint" else "pending",
            "status_note": None,
            "promotion_note": promotion_note if kind == "claim" else None,
            "stuck_reason": None,
            "revises": None,
            "created_at": clock_now(),
            "created_by": actor,
        }
        _append_node(paths, record)
        nodes[node_id] = record
        made.append(record)

    # auto-transition: a viewpoint that just got its first children starts expanding
    if parent_id is not None:
        parent = nodes[parent_id]
        if parent["kind"] == "viewpoint" and parent["status"] == "open":
            updated = {**parent, "status": "expanding", "created_at": clock_now(),
                       "created_by": actor}
            _append_node(paths, updated)
    return made


def promote(paths: Paths, session: dict[str, Any], node_id: str, note: str,
            *, actor: str | None = None) -> dict[str, Any]:
    nodes = nodes_by_id(paths)
    if node_id not in nodes:
        raise DomainError([f"unknown node: {node_id}"])
    node = nodes[node_id]
    if node["kind"] != "viewpoint":
        raise DomainError([f"{node_id} is already a claim"])
    if node["status"] not in ("open", "expanding", "synthesized"):
        raise DomainError([f"cannot promote a {node['status']} viewpoint"])
    if not note.strip():
        raise UsageError(["promotion requires --note (attempted directions / "
                          "counterfactual probe / expected evidence)"])
    if _open_claims(nodes) >= session["budgets"]["max_open_claims"]:
        raise DomainError([f"budget max_open_claims="
                           f"{session['budgets']['max_open_claims']} reached"])
    record = {**node, "kind": "claim", "status": "pending",
              "promotion_note": note, "created_at": clock_now(),
              "created_by": clock_actor(actor)}
    _append_node(paths, record)
    return record


def set_status(paths: Paths, node_id: str, status: str, *,
               note: str | None = None, reason: str | None = None,
               actor: str | None = None) -> dict[str, Any]:
    nodes = nodes_by_id(paths)
    if node_id not in nodes:
        raise DomainError([f"unknown node: {node_id}"])
    node = nodes[node_id]
    if (node["status"], status) not in LEGAL:
        legal = sorted(to for frm, to in LEGAL if frm == node["status"])
        raise DomainError([f"illegal transition {node['status']} -> {status} "
                           f"for {node_id} (legal from {node['status']}: "
                           f"{legal or ['none — use conclude/promote']})"])
    if status in NOTE_REQUIRED_STATUSES and not (note and note.strip()):
        raise UsageError([f"--note is required when setting {status} "
                          "(the tree history must stay readable)"])
    if status == "stuck" and reason not in ("evidence", "protocol"):
        raise UsageError(["stuck requires --reason evidence|protocol"])
    record = {**node, "status": status,
              "status_note": note if note else node["status_note"],
              "stuck_reason": reason if status == "stuck" else None,
              "created_at": clock_now(), "created_by": clock_actor(actor)}
    _append_node(paths, record)
    return record


def conclude(paths: Paths, session: dict[str, Any], payload: dict[str, Any], *,
             actor: str | None = None) -> tuple[dict[str, Any], list[str]]:
    """Write a synthesis record. Payload = the synthesis schema minus schema /
    synthesis_id / created_at (code assigns those; evidence ref_ids too).
    On a v2 session: evidence.doc_id must resolve to an archived entry, and a
    quote given with a doc_id is verified verbatim against the archived text —
    a miss degrades the quote to null with a warning (P7: hallucinated quotes
    never land; honest paraphrase does). Returns (record, warnings)."""
    from . import docsdb
    from .session import set_name

    warnings: list[str] = []
    v2 = set_name(session) != "v1"
    nodes = nodes_by_id(paths)
    node_id = payload.get("node_id")
    if node_id not in nodes:
        raise DomainError([f"unknown node: {node_id!r}"])
    node = nodes[node_id]
    if node["status"] not in CONCLUDABLE:
        raise DomainError([f"cannot conclude a {node['status']} node"])

    based_on = payload.get("based_on") or {}
    for child in based_on.get("children", []):
        if child not in nodes:
            raise DomainError([f"based_on.children references unknown node: {child}"])
    entries = docsdb.entries_by_id(paths) if v2 else {}
    evidence = []
    for i, ref in enumerate(based_on.get("evidence", []), 1):
        ref = dict(ref)
        ref.setdefault("ref_id", f"E-{i:02d}")
        for key in ("url", "locator", "quote", "tool", "note"):
            ref.setdefault(key, None)
        if not v2:
            if ref.get("doc_id"):
                raise DomainError(["evidence.doc_id needs schema set v2 — "
                                   "run `nd upgrade` first"])
            ref.pop("doc_id", None)
        else:
            ref.setdefault("doc_id", None)
            if ref["doc_id"] is not None:
                if ref["doc_id"] not in entries:
                    raise DomainError([f"evidence references unknown doc: {ref['doc_id']}"])
                if ref["quote"] and not docsdb.quote_ok(paths, entries[ref["doc_id"]],
                                                        ref["quote"]):
                    warnings.append(
                        f"{ref['ref_id']}: quote is not a verbatim match in "
                        f"{ref['doc_id']} — degraded to paraphrase (quote dropped)")
                    if ref["note"] is None:
                        ref["note"] = "paraphrase (quote failed verbatim check)"
                    ref["quote"] = None
        evidence.append(ref)

    all_syn = syntheses(paths)
    revises = payload.get("revises")
    if revises is not None and revises not in {s["synthesis_id"] for s in all_syn}:
        raise DomainError([f"revises references unknown synthesis: {revises}"])

    record = {
        "schema": "synthesis.v2" if v2 else "synthesis.v1",
        "synthesis_id": next_id("SYN", [s["synthesis_id"] for s in all_syn]),
        "node_id": node_id,
        "lean": payload.get("lean"),
        "summary": payload.get("summary"),
        "confidence": payload.get("confidence"),
        "based_on": {"children": based_on.get("children", []), "evidence": evidence},
        "open_questions": payload.get("open_questions", []),
        "revises": revises,
        "created_at": clock_now(),
    }
    errs = validate(record)
    if errs:
        raise DomainError(errs)
    store.append(paths.resolve(SYNTHESES), record)

    new_status = "synthesized" if node["kind"] == "viewpoint" else "concluded"
    if node["status"] != new_status:
        updated = {**node, "status": new_status, "created_at": clock_now(),
                   "created_by": clock_actor(actor)}
        _append_node(paths, updated)
    return record, warnings
