"""V2 docs store: archival + content_hash dedup + verbatim quote verification
+ tree-distance recall + summary-based compression (index carries ≤500-char
summaries; full text stays on disk and is Read on demand).

Single writer: only `nd docs ingest` (and import via the same path) appends to
docs/index.jsonl and writes docs/store/. Recall is a pure read (P8 hard)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from . import store, tree
from .clock import now as clock_now
from .errors import DomainError, UsageError
from .paths import Paths
from .schemas import validate
INDEX = "docs/index.jsonl"
STORE_DIR = "docs/store"

_WS = re.compile(r"\s+")
_TOKEN = re.compile(r"[a-z0-9]+|[一-鿿]")
# quote checking folds typographic punctuation so a PDF's curly apostrophe
# matches an agent's ASCII one (live-test-1 F5); widening only ever lets more
# true quotes through, never fewer
_PUNCT_FOLD = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"',
                             "\u201d": '"', "\u2013": "-", "\u2014": "-",
                             "\u00a0": " ", "\u2026": "..."})


def _norm(text: str) -> str:
    return _WS.sub(" ", text.translate(_PUNCT_FOLD)).strip()


def tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def entries_by_id(paths: Paths) -> dict[str, dict[str, Any]]:
    return store.latest_by_id(paths.resolve(INDEX), "doc_id")


def content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()


def _next_doc_id(entries: dict[str, Any]) -> str:
    from .ids import next_id
    return next_id("DOC", list(entries))


def ingest(paths: Paths, payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """payload: {kind, title, url?, text_file, summary, bindings:[{node_id,
    relation, note?}], origin?}. Returns (entry, warnings). Same content_hash
    ⇒ the existing entry gains the new bindings instead of a duplicate doc."""
    warnings: list[str] = []
    raw_path = payload.get("text_file") or ""
    src = Path(raw_path)
    if not src.is_absolute() and not src.is_file():
        candidate = paths.resolve(raw_path)   # session-relative works too
        if candidate.is_file():
            src = candidate
    if not src.is_file():
        raise UsageError([f"text_file not found: {raw_path} (absolute or "
                          "session-relative, e.g. notes/saved.txt)"])
    raw_bytes = src.read_bytes()
    if b"\x00" in raw_bytes:
        raise DomainError(["text_file looks binary (contains null bytes) — "
                           "archive extracted text, not a raw binary/PDF"])
    text = raw_bytes.decode("utf-8", errors="replace")
    if not text.strip():
        raise DomainError(["text_file is empty — nothing to archive"])

    nodes = tree.nodes_by_id(paths)
    raw_bindings = payload.get("bindings") or []
    if not raw_bindings:
        raise UsageError(["at least one binding {node_id, relation} is required"])
    now = clock_now()
    bindings = []
    for b in raw_bindings:
        if b.get("node_id") not in nodes:
            raise DomainError([f"binding references unknown node: {b.get('node_id')!r}"])
        bindings.append({"node_id": b["node_id"], "relation": b.get("relation"),
                         "note": b.get("note"), "bound_at": now})

    entries = entries_by_id(paths)
    chash = content_hash(text)
    existing = next((e for e in entries.values() if e["content_hash"] == chash), None)

    if existing is not None:
        merged = list(existing["bindings"])
        seen = {(b["node_id"], b["relation"]) for b in merged}
        added = 0
        for b in bindings:
            if (b["node_id"], b["relation"]) not in seen:
                merged.append(b); seen.add((b["node_id"], b["relation"])); added += 1
        if not added:
            warnings.append(f"duplicate content and bindings — {existing['doc_id']} unchanged")
            return existing, warnings
        entry = {**existing, "bindings": merged}
        warnings.append(f"content already archived as {existing['doc_id']} — "
                        f"added {added} binding(s), no new document")
    else:
        doc_id = _next_doc_id(entries)
        text_file = f"{STORE_DIR}/{doc_id}.txt"
        dest = paths.resolve(text_file)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        entry = {
            "schema": "docs.entry.v1",
            "doc_id": doc_id,
            "kind": payload.get("kind"),
            "title": payload.get("title"),
            "url": payload.get("url"),
            "content_hash": chash,
            "text_file": text_file,
            "summary": payload.get("summary"),
            "bindings": bindings,
            "origin": payload.get("origin"),
            "retrieved_at": now,
        }
    errs = validate(entry)
    if errs:
        raise DomainError(errs)
    store.append(paths.resolve(INDEX), entry)
    return entry, warnings


RELATIONS = ("supports", "refutes", "context", "background")


def bind(paths: Paths, doc_id: str, node_id: str, relation: str,
         note: str | None = None) -> tuple[dict[str, Any], list[str]]:
    """Add a binding to an already-archived doc without re-ingesting its text
    (R3). Appends a new latest record with the binding added; a duplicate
    (node, relation) is a no-op with a warning."""
    entries = entries_by_id(paths)
    if doc_id not in entries:
        raise DomainError([f"unknown doc: {doc_id}"])
    if node_id not in tree.nodes_by_id(paths):
        raise DomainError([f"unknown node: {node_id}"])
    if relation not in RELATIONS:
        raise UsageError([f"relation must be one of {list(RELATIONS)}, got {relation!r}"])
    entry = entries[doc_id]
    if any(b["node_id"] == node_id and b["relation"] == relation
           for b in entry["bindings"]):
        return entry, [f"{doc_id} is already bound to {node_id} as {relation} — unchanged"]
    updated = {**entry, "bindings": entry["bindings"] + [
        {"node_id": node_id, "relation": relation, "note": note,
         "bound_at": clock_now()}]}
    errs = validate(updated)
    if errs:
        raise DomainError(errs)
    store.append(paths.resolve(INDEX), updated)
    return updated, []


def quote_ok(paths: Paths, entry: dict[str, Any], quote: str) -> bool:
    text = paths.resolve(entry["text_file"]).read_text(encoding="utf-8",
                                                       errors="replace")
    return _norm(quote) in _norm(text)


def for_node(paths: Paths, node_id: str, *, include_ancestors: bool = True
             ) -> list[dict[str, Any]]:
    nodes = tree.nodes_by_id(paths)
    if node_id not in nodes:
        raise DomainError([f"unknown node: {node_id}"])
    wanted = set(tree.path_of(nodes, node_id)) if include_ancestors else {node_id}
    out = []
    for doc_id in sorted(entries_by_id(paths)):
        e = entries_by_id(paths)[doc_id]
        if any(b["node_id"] in wanted for b in e["bindings"]):
            out.append(e)
    return out


def _distance(nodes: dict, query_id: str, bound_id: str) -> str:
    if bound_id == query_id:
        return "self"
    if bound_id not in nodes:
        return "global"
    qpath = tree.path_of(nodes, query_id)
    bpath = tree.path_of(nodes, bound_id)
    if bpath[: len(qpath)] == qpath:
        return "descendant"
    if qpath[: len(bpath)] == bpath:
        return "ancestor"
    common = 0
    for a, b in zip(qpath, bpath):
        if a != b:
            break
        common += 1
    # sibling = the binding lives inside the query node's PARENT's subtree
    # (LCA is the direct parent); anything joined further up is global
    return "sibling" if common == len(qpath) - 1 else "global"


_ORDER = {"self": 0, "descendant": 1, "ancestor": 2, "sibling": 3, "global": 4}
_STRONG_WEIGHT = 3  # title/summary/notes count 3× an archived-body token match


def _relevance(paths: Paths, entry: dict[str, Any], qtok: set[str]) -> tuple[int, int, int]:
    """(score, strong_hits, body_hits). R2: title/summary/binding-notes are
    weighted, and the archived FULL TEXT is scored too — so a doc relevant only
    in its body still ranks (the live-test-2 G4 weakness was title+summary-only)."""
    strong = tokens(entry["title"] + " " + entry["summary"] + " "
                    + " ".join(b.get("note") or "" for b in entry["bindings"]))
    try:
        body = tokens(paths.resolve(entry["text_file"]).read_text(
            encoding="utf-8", errors="replace"))
    except OSError:
        body = set()
    strong_hits = len(qtok & strong)
    body_hits = len(qtok & body)
    return _STRONG_WEIGHT * strong_hits + body_hits, strong_hits, body_hits


def recall(paths: Paths, node_id: str, query: str, k: int = 8) -> dict[str, Any]:
    nodes = tree.nodes_by_id(paths)
    if node_id not in nodes:
        raise DomainError([f"unknown node: {node_id}"])
    qtok = tokens(query)
    scored = []
    for doc_id, e in sorted(entries_by_id(paths).items()):
        dist = min((_distance(nodes, node_id, b["node_id"]) for b in e["bindings"]),
                   key=_ORDER.get)
        score, sh, bh = _relevance(paths, e, qtok)
        # sort key: distance tier first (design), then relevance desc, then id
        scored.append((_ORDER[dist], -score, doc_id, dist, score, sh, bh, e))
    scored.sort(key=lambda t: t[:3])
    hits = []
    for _, _, doc_id, dist, score, sh, bh, e in scored[:k]:
        why = (f"distance {dist}; relevance {score} "
               f"(strong×{_STRONG_WEIGHT}={sh * _STRONG_WEIGHT}, body={bh})")
        if score == 0:
            why += " — NO query-token match"
        hits.append({"doc_id": doc_id, "title": e["title"], "summary": e["summary"],
                     "text_file": e["text_file"], "distance": dist, "why": why})
    result = {"schema": "recall.result.v1", "node_id": node_id, "query": query,
              "hits": hits}
    errs = validate(result)
    if errs:  # shape bug in nd itself
        raise AssertionError(f"internal: invalid recall result: {errs}")
    return result
