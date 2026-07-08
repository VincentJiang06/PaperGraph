"""The evidence matcher + request fingerprint (docs/04 §Memoized Search).

The matcher is intentionally dumb and deterministic (no embeddings in v1): its
misses cost one docs round-trip; its determinism buys reproducible packs. Both
functions cite ``textutil`` (docs/09 §0) — no improvised tokenizer here.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from typing import Any, Optional, Sequence

from ..textutil import scope_compatible, tokens

_WHITESPACE_RE = re.compile(r"\s+")

# S5 hybrid retrieval contract constants (docs/18). Changing any is a spec change.
ALPHA = 0.6  # weight on the semantic (sscore) half of the hybrid score
TAU = 0.35  # semantic inclusion floor
KEYWORD_RAW_MIN = 2  # raw keyword-token-overlap inclusion floor (docs/04)
CLUSTER_TAU = 0.92  # within-document near-duplicate cosine floor (V-SEM-05)


# --- evidence matcher (DocsPack assembly, `docs build-pack`) -----------------


def _eu_haystack(eu: dict[str, Any]) -> set[str]:
    """tokens(EU.summary) ∪ tokens(EU.quote_or_paraphrase) ∪ tokens(join(can_cite_for))."""
    toks: set[str] = set()
    toks |= set(tokens(eu.get("summary", "") or ""))
    toks |= set(tokens(eu.get("quote_or_paraphrase", "") or ""))
    toks |= set(tokens(" ".join(eu.get("can_cite_for", []) or [])))
    return toks


def score(claim: str, eu: dict[str, Any]) -> int:
    """|tokens(claim) ∩ (tokens(summary) ∪ tokens(quote) ∪ tokens(can_cite_for))|."""
    return len(set(tokens(claim or "")) & _eu_haystack(eu))


def match(
    claim: str, target_scope: dict[str, Any] | None, evidence_units: list[dict[str, Any]]
) -> list[tuple[int, dict[str, Any]]]:
    """Return the included (score, EU) pairs for a target claim.

    include EU iff score(EU) >= 2 AND scope_compatible(EU.scope, target.scope);
    order by (score desc, evidence_id asc); no cap in v1 (graphs are small).
    """
    scored: list[tuple[int, dict[str, Any]]] = []
    for eu in evidence_units:
        s = score(claim, eu)
        if s >= 2 and scope_compatible(eu.get("scope", {}) or {}, target_scope or {}):
            scored.append((s, eu))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("evidence_id", "")))
    return scored


# --- S5 hybrid scoring (docs/18) --------------------------------------------
#
# Pure Python (NO numpy) so the scoring/ordering/clustering MATH is testable on
# synthetic vectors in the DEFAULT suite — the embedding production (db/semantic)
# is the only place that needs onnxruntime/numpy. Vectors here are any float
# sequence (a list in tests, an np.ndarray from the parquet at runtime).

Vector = Sequence[float]


def _cosine(a: Vector, b: Vector) -> float:
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        fx, fy = float(x), float(y)
        dot += fx * fy
        na += fx * fx
        nb += fy * fy
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _minmax(values: dict[str, float]) -> dict[str, float]:
    """Min-max normalize raw keyword scores over the candidate set (docs/18).
    Degenerate range (all equal): maximal→1.0 if positive, else 0.0."""
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    if hi <= lo:
        return {k: (1.0 if v > 0 else 0.0) for k, v in values.items()}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def hybrid_score(
    claim: str,
    target_scope: dict[str, Any] | None,
    evidence_units: list[dict[str, Any]],
    eu_vectors: dict[str, Vector] | None,
    claim_vector: Optional[Vector],
) -> tuple[list[tuple[float, dict[str, Any]]], dict[str, dict[str, float]]]:
    """Hybrid keyword+embedding scoring at pack build (docs/18).

    kscore(EU)  := keyword score (docs/04), min-max normalized over candidates
    sscore(EU)  := cosine(claim_vec, eu_vec) clamped [0,1] (0 when no vector)
    score(EU)   := ALPHA·sscore + (1-ALPHA)·kscore
    include EU  iff (sscore ≥ TAU OR raw-keyword ≥ 2) AND scope_compatible
    order       (score desc, evidence_id asc)

    Returns (included_ordered, scores_by_id) where scores_by_id spans every
    scope-compatible candidate ({sscore, kscore, raw_kscore, score})."""
    candidates = [
        eu for eu in evidence_units
        if scope_compatible(eu.get("scope", {}) or {}, target_scope or {})
    ]
    raw_k = {eu["evidence_id"]: float(score(claim, eu)) for eu in candidates}
    kn = _minmax(raw_k)
    eu_vectors = eu_vectors or {}

    scores_by_id: dict[str, dict[str, float]] = {}
    included: list[tuple[float, dict[str, Any]]] = []
    for eu in candidates:
        eid = eu["evidence_id"]
        vec = eu_vectors.get(eid)
        ss = _clamp01(_cosine(claim_vector, vec)) if (vec is not None and claim_vector is not None) else 0.0
        ks = kn[eid]
        sc = ALPHA * ss + (1.0 - ALPHA) * ks
        scores_by_id[eid] = {"sscore": ss, "kscore": ks, "raw_kscore": raw_k[eid], "score": sc}
        if ss >= TAU or raw_k[eid] >= KEYWORD_RAW_MIN:
            included.append((sc, eu))
    included.sort(key=lambda pair: (-pair[0], pair[1]["evidence_id"]))
    return included, scores_by_id


def cluster_near_dups(
    eus: list[dict[str, Any]],
    eu_vectors: dict[str, Vector] | None,
    tau: float = CLUSTER_TAU,
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    """Within ONE document, collapse EUs with cosine ≥ tau to one representative
    (V-SEM-05). Across documents NEVER cluster. Representative = longest
    can_cite_for; tie → lowest evidence_id (deterministic).

    Returns (kept, also_map): ``kept`` preserves the input order minus dropped
    members; ``also_map[rep_id]`` = sorted dropped ids for that cluster. With no
    vectors (keyword.v1) nothing clusters — every EU is its own representative."""
    eu_vectors = eu_vectors or {}
    by_doc: dict[str, list[dict[str, Any]]] = {}
    for eu in eus:
        by_doc.setdefault(eu.get("doc_id") or "", []).append(eu)

    dropped: set[str] = set()
    also_map: dict[str, list[str]] = {}
    for _doc, members in by_doc.items():
        # union-find over members sharing cosine >= tau (within this document only)
        n = len(members)
        parent = list(range(n))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(n):
            vi = eu_vectors.get(members[i]["evidence_id"])
            if vi is None:
                continue
            for j in range(i + 1, n):
                vj = eu_vectors.get(members[j]["evidence_id"])
                if vj is None:
                    continue
                if _cosine(vi, vj) >= tau:
                    parent[find(i)] = find(j)

        clusters: dict[int, list[dict[str, Any]]] = {}
        for i in range(n):
            clusters.setdefault(find(i), []).append(members[i])
        for group in clusters.values():
            if len(group) < 2:
                continue
            rep = min(group, key=lambda e: (-len(e.get("can_cite_for", []) or []), e["evidence_id"]))
            others = sorted(e["evidence_id"] for e in group if e["evidence_id"] != rep["evidence_id"])
            also_map[rep["evidence_id"]] = others
            dropped.update(others)

    kept = [eu for eu in eus if eu["evidence_id"] not in dropped]
    return kept, also_map


# --- request-level fingerprint (docs/04) ------------------------------------


def _fp_normalize(s: str) -> str:
    """NFC, lowercase, collapse whitespace (docs/04 fingerprint normalize)."""
    s = unicodedata.normalize("NFC", s).lower()
    s = _WHITESPACE_RE.sub(" ", s)
    return s.strip()


def fingerprint(need: str, search_hints: list[str] | None) -> str:
    """sha256 over normalize(need) + "\\n" + sorted normalized search_hints."""
    hints = sorted(_fp_normalize(h) for h in (search_hints or []))
    payload = _fp_normalize(need) + "\n" + "\n".join(hints)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
