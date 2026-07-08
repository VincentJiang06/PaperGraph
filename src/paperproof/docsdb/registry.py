"""Source Registry — tiers, fetch recipes, provenance (docs/16, S3 Stage A-lite).

The registry is the project's durable memory of *where evidence lives, how to
fetch it, and how much it counts* (`docs/sources.jsonl`). It is append-only and
latest-per-domain. Two writers:

  * the Docs ingestor LEARNS a new SourceProfile version on every ingested
    Document (tier via the fixed source_type->tier table, ``blocked_direct`` from
    the docs-result log, fetch method from provenance);
  * ``docs source set`` appends human curation (a tier/workaround).

Only Stage A-lite (registry + recipes + provenance) is adopted; Stage B
triangulation (V-SRC-04) is NOT built here (docs/16, docs/00 adoption entry).
"""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlsplit

from ..clock import now as clock_now
from ..ids import next_id
from ..paths import Paths
from ..schemas.docs import SourceProfile
from ..store import jsonl

SOURCES = "docs/sources.jsonl"

# --- fixed source_type -> tier table (docs/16 §deltas, doc-synced) ----------
# docs/16 prints the tier enum but not the mapping; it is pinned here and in the
# doc (docs/16 "source_type -> tier") so the ingestor's learning is deterministic.
TIER_TABLE: dict[str, str] = {
    "official_report": "T1_official",
    "peer_reviewed": "T2_peer_reviewed",
    "working_paper": "T3_working_paper",
    "dataset": "T4_industry_data",
    "news": "T5_press",
    "user_notes": "T6_other",
}

# Authority rank: T1 is the most authoritative (rank 1). Auto-learning only ever
# RAISES a domain's tier (keeps the most authoritative source_type seen); it
# never lowers silently (V-SRC-03).
TIER_RANK: dict[str, int] = {
    "T1_official": 1, "T2_peer_reviewed": 2, "T3_working_paper": 3,
    "T4_industry_data": 4, "T5_press": 5, "T6_other": 6,
}

_BLOCK_RE = re.compile(r"\b(403|blocked|block|forbidden|denied|captcha|429)\b", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Common TLDs are not identifying labels — a domain matches a facet on its
# primary label (e.g. `adp` from `adp.com`), never on `com`.
_TLDS = {"com", "org", "net", "gov", "edu", "io", "co", "uk", "us", "int", "ac"}


def tier_for(source_type: str) -> str:
    """Map a Document.source_type to its registry tier (fixed table)."""
    return TIER_TABLE.get(source_type, "T6_other")


def domain_from_url(url: Optional[str]) -> Optional[str]:
    """The registrable host of a web origin URL (lower-cased, ``www.`` stripped);
    ``None`` when there is no URL (user-provided local files have no domain)."""
    if not url:
        return None
    host = urlsplit(url if "//" in url else "//" + url).hostname
    if not host:
        return None
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


# --- reads ------------------------------------------------------------------


def load_all(paths: Paths) -> list[dict[str, Any]]:
    """Every SourceProfile record in append order (for V-SRC-03 history checks)."""
    return jsonl.read_all(paths.resolve(SOURCES))


def load_latest(paths: Paths) -> list[dict[str, Any]]:
    """Latest SourceProfile per domain (the live registry)."""
    return jsonl.latest_records(paths.resolve(SOURCES), "domain")


def _latest_by_domain(paths: Paths) -> dict[str, dict[str, Any]]:
    return jsonl.latest_by_id(paths.resolve(SOURCES), "domain")


# --- blocked-signal learning (DEFENSIVE S1 query_log integration point) -----
# `blocked_direct` is learned from the query/search log — an S1 artifact. This
# worktree carries docs_result.v1 (`search_log: [str]`); S1's docs_result.v2 will
# carry `query_log: [{outcome, ...}]`. This reads block signals from WHICHEVER
# the result presents, so the two builds merge cleanly.


def _blocked_texts(result: dict[str, Any]) -> list[str]:
    """Lower-cased log texts that evidence a blocked/denied automated fetch,
    drawn from search_log strings OR query_log entries (outcome=='blocked')."""
    out: list[str] = []
    for line in result.get("search_log") or []:
        if isinstance(line, str) and _BLOCK_RE.search(line):
            out.append(line.lower())
    for entry in result.get("query_log") or []:
        if not isinstance(entry, dict):
            continue
        blob = " ".join(
            str(entry.get(k, "")) for k in ("outcome", "domain", "url", "query", "note")
        ).lower()
        if entry.get("outcome") == "blocked" or _BLOCK_RE.search(blob):
            out.append(blob)
    return out


def _domain_blocked(domain: str, blocked_texts: list[str]) -> bool:
    d = domain.lower()
    return any(d in t for t in blocked_texts)


# --- learning (the ingestor upserts a domain's profile) ---------------------


def learn(
    paths: Paths,
    doc_domains: list[tuple[str, str]],
    result: dict[str, Any] | None,
    now: str | None = None,
) -> dict[str, str]:
    """Upsert (append a new version of) the SourceProfile for every domain seen
    in an ingest. ``doc_domains`` is (domain, source_type) per archived Document
    that carries a domain. Returns {domain: resulting_tier} for provenance
    denormalization. One appended version per domain per ingest event.
    """
    now = now or clock_now()
    blocked_texts = _blocked_texts(result or {})

    # aggregate this ingest's encounters per domain.
    encounters: dict[str, int] = {}
    seen_types: dict[str, list[str]] = {}
    for domain, stype in doc_domains:
        encounters[domain] = encounters.get(domain, 0) + 1
        seen_types.setdefault(domain, []).append(stype)

    latest = _latest_by_domain(paths)
    existing_ids = [r["source_id"] for r in load_all(paths)]
    resulting: dict[str, str] = {}
    for domain in sorted(encounters):
        prev = latest.get(domain)
        # most authoritative tier: prior tier vs the source_types seen this round.
        candidate_tiers = [tier_for(t) for t in seen_types[domain]]
        if prev is not None:
            candidate_tiers.append(prev["tier"])
        new_tier = min(candidate_tiers, key=lambda t: TIER_RANK[t])

        source_id = prev["source_id"] if prev else next_id("SRC", existing_ids)
        if not prev:
            existing_ids.append(source_id)
        blocked = bool(prev and prev.get("fetch", {}).get("blocked_direct")) or _domain_blocked(
            domain, blocked_texts
        )
        workarounds = list((prev or {}).get("fetch", {}).get("workarounds", []) or [])
        seen_count = int((prev or {}).get("seen_count", 0)) + encounters[domain]
        publisher = (prev or {}).get("publisher", "") or ""
        tier_note = None
        if prev and prev["tier"] != new_tier:
            tier_note = f"auto: raised {prev['tier']} -> {new_tier} (source_type seen from {domain})"

        record = SourceProfile(
            source_id=source_id, project_id=paths.project_id, domain=domain,
            publisher=publisher, tier=new_tier,
            fetch={"blocked_direct": blocked, "workarounds": workarounds},
            seen_count=seen_count, last_ok_fetch_method="direct",
            tier_note=tier_note, created_at=now,
        )
        jsonl.append(paths.resolve(SOURCES), record)
        resulting[domain] = new_tier
    return resulting


# --- dispatch excerpt (registry-in-prompt) [V-SRC-05] -----------------------


def _facet_text(need: str, hints: list[str] | None, scope: dict[str, Any] | None) -> str:
    parts = [need or ""]
    parts += list(hints or [])
    for v in (scope or {}).values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts += [str(x) for x in v]
    return " ".join(parts).lower()


def profile_matches_facets(profile: dict[str, Any], facet_text: str) -> bool:
    """A profile is dispatch-relevant iff it is T1 (every T1 profile ships) OR its
    domain / publisher appears in the request's facets (docs/16 V-SRC-05).

    A facet matches on the full domain, the publisher string, or the domain's
    primary label as a whole token (``adp`` from ``adp.com``)."""
    if profile.get("tier") == "T1_official":
        return True
    dom = (profile.get("domain") or "").lower()
    pub = (profile.get("publisher") or "").lower()
    if dom and dom in facet_text:
        return True
    if pub and pub in facet_text:
        return True
    tokens = set(_TOKEN_RE.findall(facet_text))
    labels = [lbl for lbl in dom.split(".") if lbl and lbl not in _TLDS]
    return any(lbl in tokens for lbl in labels)


def matched_profiles(
    paths: Paths, need: str, hints: list[str] | None = None, scope: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """The dispatch registry excerpt for a DocsRequest: every T1 profile + every
    profile whose domain/publisher matches a request facet, domain-sorted."""
    facet_text = _facet_text(need, hints, scope)
    hits = [p for p in load_latest(paths) if profile_matches_facets(p, facet_text)]
    return sorted(hits, key=lambda p: p.get("domain", ""))


def render_excerpt(profiles: list[dict[str, Any]]) -> str:
    """Render the read-only REGISTRY block that fills the docs_worker `{registry}`
    placeholder. Lawful public-access recipes only (never paywall bypass)."""
    if not profiles:
        return "(registry empty — no learned sources yet)"
    lines: list[str] = []
    for p in profiles:
        fetch = p.get("fetch", {}) or {}
        recipes = "; ".join(
            f"{w['kind']}({w['note']})" for w in (fetch.get("workarounds") or [])
        ) or "none recorded"
        blocked = "blocks-direct" if fetch.get("blocked_direct") else "direct-ok"
        lines.append(
            f"- {p.get('domain')} [{p.get('tier')}] {blocked}; workarounds: {recipes}"
        )
    return "\n".join(lines)
