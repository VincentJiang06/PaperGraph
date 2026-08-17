"""S2 Search Orchestra — waves, deterministic merger, coverage verdict (docs/15).

A DocsRequest with ``fan`` becomes a WAVE: one member per angle (each a
docs_queue WorkItem + an angle-specific S1 plan + a DISTINCT output path
[V-WAVE-01]), a DETERMINISTIC merger (code, no LLM), and a fresh adversarial
coverage critic whose closed form drives the CODE-computed verdict over ≤2
bounded rounds.

Deterministic pieces (NO LLM): ``merge_results`` (the merger), ``wave_verdict``
(the verdict), ``followup_specs`` (what a follow-up round opens). The critic is
the only LLM and it only fills ``coverage_report.v1``; code does the rest.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..errors import DomainError
from ..ids import next_id
from ..paths import Paths
from ..queue import engine
from ..schemas.search import SearchWave
from ..store import jsonl
from ..textutil import normalize
from . import ingest, planner

WAVES = "docs/waves.jsonl"
MERGED_DIR = "docs/merged"
COVERAGE_DIR = "agent_outputs/coverage_reports"
DOCS_REQUESTS = "docs/docs_requests.jsonl"

DOCS_QUEUE = "docs_queue"
CRITIC_QUEUE = "critic_queue"

# The mandatory fan angles (docs/15 §Wave expansion). ``news`` joins only when
# the claim's period touches the last 18 months.
MANDATORY_ANGLES: tuple[str, ...] = ("official_stats", "academic", "industry", "counter")
R_MAX = 2

# The frozen tracking-param strip list (docs/15 §Merger). utm_* is a prefix rule.
_TRACKING_EXACT = {"gclid", "fbclid", "ref"}
_DEFAULT_PORT = {"http": 80, "https": 443}
_MULTISLASH_RE = re.compile(r"/{2,}")


# --- canonicalization + hashing --------------------------------------------


def _content_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _is_tracking(key: str) -> bool:
    k = key.lower()
    return k in _TRACKING_EXACT or k.startswith("utm_")


def canonical_url(url: str | None) -> str | None:
    """Canonical URL for dedup (docs/15 §Merger): lowercase scheme+host, strip
    ``www.`` (consistent with ``registry.domain_from_url``), default a scheme,
    strip default port, strip fragment, strip the frozen tracking-param list
    ({utm_*, gclid, fbclid, ref}), collapse duplicate slashes, strip one
    trailing slash. Deterministic and TOTAL — a malformed port (F5/D7: the live
    ValueError crash) falls back to the raw netloc instead of raising."""
    if not url:
        return None
    raw = url.strip()
    if "//" not in raw:
        raw = "//" + raw  # scheme-less: treat the head as a host, like the registry
    parts = urlsplit(raw)
    scheme = parts.scheme.lower() or "https"
    try:
        host = (parts.hostname or "").lower()
        port = parts.port
    except ValueError:  # malformed port ("example.com:8o8") — total, never a crash
        netloc = parts.netloc.lower()
    else:
        netloc = host
        if port is not None and port != _DEFAULT_PORT.get(scheme):
            netloc = f"{host}:{port}"
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = _MULTISLASH_RE.sub("/", parts.path)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _is_tracking(k)])
    return urlunsplit((scheme, netloc, path, query, ""))


# --- the merger (deterministic; the golden-tested core) ---------------------


def merge_results(request_id: str, project_id: str, member_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge a wave's per-member docs_result dicts into ONE docs_result.v2
    (docs/15 §Merger). Same member set ⇒ byte-identical output [V-WAVE-02].

    1. concat documents; dedup by content_hash ONLY (first-seen representative
       wins, member order then doc order). A canonical-URL collision with a
       DIFFERING content_hash keeps BOTH docs (F5/D7): re-pointing a quote EU
       onto another member's text broke V-DR-05 at ingest_merged and wedged the
       wave closed-less;
    2. concat EUs; re-point doc_refs to the deduped table; drop exact-dup EUs
       (same doc, same normalized quote);
    3. order docs by content_hash asc, EUs by (doc order, location, quote hash).
    """
    reps: list[dict[str, Any]] = []          # representative docs, first-seen order
    rep_ch: list[str] = []                    # each rep's own content_hash
    key_of_content: dict[str, int] = {}
    member_doc_key: dict[tuple[int, int], int] = {}

    for m, res in enumerate(member_results):
        for i, doc in enumerate(res.get("documents", []) or []):
            ch = _content_hash(doc.get("text") or "")
            k = key_of_content.get(ch)
            if k is None:
                k = len(reps)
                reps.append(doc)
                rep_ch.append(ch)
            key_of_content.setdefault(ch, k)
            member_doc_key[(m, i)] = k

    # order docs by content_hash asc (reps are pairwise distinct content_hashes)
    order = sorted(range(len(reps)), key=lambda k: rep_ch[k])
    rep_to_final = {k: fi for fi, k in enumerate(order)}
    merged_docs = [
        {
            "title": reps[k].get("title"),
            "source_type": reps[k].get("source_type"),
            "origin": reps[k].get("origin"),
            "citation_key": reps[k].get("citation_key"),
            "text": reps[k].get("text"),
        }
        for k in order
    ]

    # re-point EUs to the deduped/re-ordered table
    raw_eus: list[dict[str, Any]] = []
    for m, res in enumerate(member_results):
        for eu in res.get("evidence_units", []) or []:
            new_eu = {
                "doc_ref": None,
                "doc_id": None,
                "location": eu.get("location"),
                "kind": eu.get("kind"),
                "quote_or_paraphrase": eu.get("quote_or_paraphrase"),
                "summary": eu.get("summary"),
                "support_direction": eu.get("support_direction"),
                "can_cite_for": list(eu.get("can_cite_for") or []),
                "cannot_cite_for": list(eu.get("cannot_cite_for") or []),
                "scope": eu.get("scope") or {},
            }
            if eu.get("doc_ref") is not None:
                new_eu["doc_ref"] = rep_to_final[member_doc_key[(m, eu["doc_ref"])]]
            else:
                new_eu["doc_id"] = eu.get("doc_id")
            raw_eus.append(new_eu)

    def _norm_quote(eu: dict[str, Any]) -> str:
        return normalize(eu.get("quote_or_paraphrase") or "")

    def _sort_key(eu: dict[str, Any]) -> tuple:
        doc_key = (0, eu["doc_ref"]) if eu["doc_ref"] is not None else (1, eu.get("doc_id") or "")
        qh = hashlib.sha256(_norm_quote(eu).encode("utf-8")).hexdigest()
        return (doc_key, eu.get("location") or "", qh)

    raw_eus.sort(key=_sort_key)
    merged_eus: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    for eu in raw_eus:
        ident = ("ref", eu["doc_ref"]) if eu["doc_ref"] is not None else ("id", eu.get("doc_id"))
        key = (ident, _norm_quote(eu))
        if key in seen:  # drop exact-dup EU (same doc, same normalized quote)
            continue
        seen.add(key)
        merged_eus.append(eu)

    # concat member query_logs (V-SP is not re-run on the merged result); the
    # search record is non-empty so a not_found merge still satisfies V-DR-06.
    query_log: list[dict[str, Any]] = []
    for res in member_results:
        query_log += list(res.get("query_log") or [])
    if not query_log:
        query_log = [{"qid": "MERGED", "executed": True, "outcome": "empty",
                      "urls_seen": 0, "docs_taken": 0, "note": "no member query logs"}]

    not_found = not merged_docs and not merged_eus
    return {
        "schema_version": "docs_result.v2",
        "request_id": request_id,
        "project_id": project_id,
        "documents": merged_docs,
        "evidence_units": merged_eus,
        "not_found": not_found,
        "query_log": query_log,
    }


# --- the verdict (deterministic; CODE computes it, never the critic) --------


def wave_verdict(form: dict[str, Any], round: int, r_max: int = R_MAX,
                 mandatory: tuple[str, ...] = MANDATORY_ANGLES) -> str:
    """The wave verdict (docs/15). Returns ``sufficient | followup | closed``.

    sufficient  iff every mandatory angle ∈ {yes, tried_empty, tried_blocked}
                AND disconfirming_captured ∈ {yes, n/a}
                AND (primary_source_present = yes OR round = R_MAX)
    followup    otherwise while round < R_MAX
    closed      at R_MAX regardless (no infinite loop).
    """
    ac = form.get("angle_covered", {}) or {}
    ok = {"yes", "tried_empty", "tried_blocked"}
    every_ok = all(ac.get(a) in ok for a in mandatory)
    disc_ok = form.get("disconfirming_captured") in ("yes", "n/a")
    primary_ok = form.get("primary_source_present") == "yes"
    if every_ok and disc_ok and (primary_ok or round >= r_max):
        return "sufficient"
    if round < r_max:
        return "followup"
    return "closed"


def followup_specs(form: dict[str, Any], expected_sources: list[dict[str, Any]],
                   mandatory: tuple[str, ...] = MANDATORY_ANGLES) -> list[dict[str, Any]]:
    """One follow-up member per no_attempt angle + one per expected_source
    (its suggested_query becomes a hint) — docs/15. Each spec carries the
    origin the follow-up member cites in the wave record [V-WAVE-04].

    Duplicate expected_source NAMES are index-discriminated (``#2``, ``#3`` …)
    so origins — and therefore member output paths and plan ids, which derive
    from the origin (F6/D8) — stay pairwise unique [V-WAVE-01]."""
    ac = form.get("angle_covered", {}) or {}
    specs: list[dict[str, Any]] = []
    for a in mandatory:
        if ac.get(a) == "no_attempt":
            specs.append({"angle": a, "origin": f"angle:{a}", "hint": None})
    name_counts: dict[str, int] = {}
    for es in expected_sources or []:
        name = str(es.get("name") or "unnamed")
        n = name_counts.get(name, 0) + 1
        name_counts[name] = n
        label = name if n == 1 else f"{name}#{n}"
        specs.append({"angle": "official_stats",
                      "origin": f"expected_source:{label}",
                      "hint": es.get("suggested_query")})
    return specs


# --- wave record storage ----------------------------------------------------


def load_waves(paths: Paths) -> list[dict[str, Any]]:
    return jsonl.latest_records(paths.resolve(WAVES), "wave_id")


def wave_by_id(paths: Paths, wave_id: str) -> dict[str, Any] | None:
    return jsonl.latest_by_id(paths.resolve(WAVES), "wave_id").get(wave_id)


def wave_for_request(paths: Paths, request_id: str) -> dict[str, Any] | None:
    for w in load_waves(paths):
        if w.get("request_id") == request_id:
            return w
    return None


def _append_wave(paths: Paths, wave: dict[str, Any]) -> dict[str, Any]:
    jsonl.append(paths.resolve(WAVES), SearchWave.model_validate(wave))
    return wave


def _news_applicable(paths: Paths, request: dict[str, Any]) -> bool:
    """news joins the fan only when the claim's period touches the last 18
    months (docs/15). Period comes from the target node's scope; parsed as a
    ``YYYY`` or ``YYYY-YYYY`` range against the clock year."""
    from ..graph import model as graph_model  # local: avoid import cycle

    rec = graph_model.load(paths).record(request.get("target_id"))
    scope = (rec.get("scope") or {}) if (rec and "node_id" in rec) else {}
    period = scope.get("period")
    if not period:
        return False
    years = [int(y) for y in re.findall(r"\d{4}", str(period))]
    if not years:
        return False
    now_year = int(clock_now()[:4])
    # last 18 months ≈ the current year or the one before it.
    return max(years) >= now_year - 1


# --- start a wave -----------------------------------------------------------


def _angles_for(paths: Paths, request: dict[str, Any], fan: bool) -> list[str]:
    if not fan:
        return [planner.DEFAULT_ANGLE]  # reactive single member, unchanged behaviour
    angles = list(MANDATORY_ANGLES)
    if _news_applicable(paths, request):
        angles.append("news")
    return angles


def _cancel_pending_single_items(paths: Paths, request_id: str, keep: set[str], actor: str) -> None:
    """Cancel a pre-existing open single docs item for this DR (e.g. the one
    `docs request` created) so the wave owns the search. Orchestrator/sweep DRs
    carry no dependent re-proof, so cancellation is inert there."""
    for item in engine.load_items(paths):
        if (item.get("queue_name") == DOCS_QUEUE and item.get("target_id") == request_id
                and item["work_item_id"] not in keep
                and item.get("status") in ("queued", "blocked")):
            engine.cancel(paths, item["work_item_id"], actor, detail={"reason": "superseded_by_wave"})


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def member_plan_id(request_id: str, angle: str, round: int, origin: str | None) -> str:
    """A wave member's plan id (F6/D8): round-1 members keep the bare
    ``SP-<request>-<angle>``; a round>1 follow-up appends the SAME
    ``.r<round>.<origin-slug>`` discriminator as its output path, so a follow-up
    NEVER reuses (reprints) the round-1 plan and two same-angle follow-ups get
    distinct plans/task_ids."""
    base = f"SP-{request_id}-{angle}"
    if round > 1:
        token = _SLUG_RE.sub("-", (origin or angle).lower()).strip("-") or angle
        base = f"{base}.r{round}.{token}"
    return base


def member_output(request_id: str, angle: str, round: int, origin: str | None) -> str:
    """A wave member's declared output path (docs/15 §Wave expansion). Round-1
    members keep the bare per-angle path
    ``agent_outputs/docs_results/DR-x.<angle>.docs_result.json``; a round>1
    follow-up gets a ``.r<round>.<origin-slug>`` discriminator so it NEVER
    reuses — and silently overwrites — a round-1 member's committed result, and
    two follow-ups (a reopened angle vs an expected_source) never collide either
    [V-WAVE-01]. The origin (``angle:<name>`` / ``expected_source:<name>``) is
    pairwise-distinct within a round, so the path is too."""
    stem = f"{request_id}.{angle}"
    if round > 1:
        token = _SLUG_RE.sub("-", (origin or angle).lower()).strip("-") or angle
        stem = f"{stem}.r{round}.{token}"
    return f"agent_outputs/docs_results/{stem}.docs_result.json"


def _open_member(paths: Paths, request_id: str, angle: str, round: int, origin: str | None,
                 hint: str | None, actor: str) -> dict[str, Any]:
    plan = planner.plan_for_wave_member(paths, request_id, angle,
                                        extra_hints=[hint] if hint else None,
                                        plan_id=member_plan_id(request_id, angle, round, origin))
    output = member_output(request_id, angle, round, origin)
    item = engine.enqueue(paths, queue_name=DOCS_QUEUE, target_type="request", target_id=request_id,
                          task_id=plan["plan_id"], output_files=[output], actor=actor)
    return {"angle": angle, "work_item_id": item["work_item_id"], "plan_id": plan["plan_id"],
            "round": round, "origin": origin}


def start_wave(paths: Paths, request_id: str, fan: bool = False, actor: str | None = None) -> dict[str, Any]:
    """`docs wave --request <DR> [--fan]`: turn a DocsRequest into a wave —
    one member per angle, each a docs_queue item + angle plan + distinct output
    [V-WAVE-01] — and append the search_wave.v1 record (status=open, round 1)."""
    actor = actor or clock_actor()
    req = jsonl.latest_by_id(paths.resolve(DOCS_REQUESTS), "request_id").get(request_id)
    if req is None:
        raise DomainError([f"docs request not found: {request_id}"])
    if wave_for_request(paths, request_id) is not None:
        raise DomainError([f"a wave already exists for request {request_id}"])
    fan_effective = bool(fan or req.get("fan"))
    angles = _angles_for(paths, req, fan_effective)

    # the wave owns the search: cancel any pre-existing open single docs item for
    # this DR (e.g. the one `docs request` created). Distinct member outputs
    # (one per angle) satisfy [V-WAVE-01].
    _cancel_pending_single_items(paths, request_id, keep=set(), actor=actor)

    members = [_open_member(paths, request_id, a, 1, None, None, actor) for a in angles]
    wave_id = next_id("WV", [w["wave_id"] for w in jsonl.read_all(paths.resolve(WAVES))])
    wave = {
        "schema_version": "search_wave.v1", "wave_id": wave_id, "request_id": request_id,
        "project_id": paths.project_id, "round": 1, "members": members,
        "status": "open", "created_at": clock_now(),
    }
    return _append_wave(paths, wave)


# --- member completion (validate; NOT ingested — only the merge is) ---------


def _member_angle(wave: dict[str, Any], wi_id: str) -> str | None:
    for mem in wave.get("members", []):
        if mem["work_item_id"] == wi_id:
            return mem["angle"]
    return None


def wave_for_member(paths: Paths, wi_id: str) -> dict[str, Any] | None:
    """The wave (latest version) whose member set contains ``wi_id`` (F2)."""
    for w in load_waves(paths):
        if any(m.get("work_item_id") == wi_id for m in w.get("members", [])):
            return w
    return None


def complete_member(paths: Paths, wave_id: str, wi_id: str, actor: str | None = None) -> dict[str, Any]:
    """Validate one wave member's docs_result against its ANGLE plan (V-PATH +
    V-DR + V-SP) and drive it to a terminal state WITHOUT ingesting (only the
    merged result is ingested — V-WAVE-05). Member results stay in
    agent_outputs as provenance."""
    from ..validate.rules import v_dr, v_path, v_sp

    actor = actor or clock_actor()
    wave = wave_by_id(paths, wave_id)
    if wave is None:
        raise DomainError([f"wave not found: {wave_id}"])
    wi = engine.get_item(paths, wi_id)
    if wi["status"] in ("claimed", "running"):
        wi = engine.complete(paths, wi_id, actor)
    elif wi["status"] != "validating":
        raise DomainError([f"wave member not in validating state: {wi_id} ({wi['status']})"])

    relpath = wi["output_files"][0]
    p = paths.project_dir / relpath
    raw = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    failures = list(v_path.check_output_path(relpath, wi.get("output_files", [])))
    failures += v_path.check_path_safety(paths.project_dir, relpath)
    vpath03 = v_path.check_utf8_json(paths.project_dir, relpath)
    failures += vpath03
    lease = wi.get("lease") or {}
    if lease.get("manifest"):
        failures += v_path.check_lease_scan(paths.project_dir, lease["manifest"])
    if not vpath03:
        failures += v_dr.raw_scan(raw)
        existing = jsonl.latest_records(paths.resolve(ingest.DOCUMENTS), "doc_id")
        archived_ids = {d["doc_id"] for d in existing}
        archived_texts = {
            d["doc_id"]: paths.resolve(d["text_path"]).read_text(encoding="utf-8")
            for d in existing if d.get("text_path") and paths.resolve(d["text_path"]).exists()
        }
        failures += v_dr.check(raw, archived_doc_ids=archived_ids, archived_texts=archived_texts)
        if raw.get("schema_version") == "docs_result.v2":
            # F2/D2: the member is validated against ITS OWN plan, resolved from
            # the item's task_id (a follow-up member's plan id is round/origin-
            # discriminated); the angle lookup is only a legacy fallback.
            task_id = str(wi.get("task_id") or "")
            plan = planner.load_plan_by_id(paths, task_id) if task_id.startswith("SP-") else None
            if plan is None:
                angle = _member_angle(wave, wi_id)
                plan = planner.load_wave_plan(paths, wave["request_id"], angle) if angle else None
            failures += v_sp.check(raw, plan)

    if failures:
        from ..validate.envelope import to_envelope

        env = to_envelope(failures)
        engine.validate_fail(paths, wi_id, env["failed_rules"], actor, detail=env["detail"])
        raise DomainError(env["failed_rules"], data={"failed_rules": env["failed_rules"], "detail": env["detail"]})

    engine.validate_pass(paths, wi_id, actor, detail={"wave_id": wave_id, "wave_member": True})
    engine.commit_item(paths, wi_id, actor)
    return {"wave_id": wave_id, "work_item_id": wi_id, "committed": True}


def _members_terminal(paths: Paths, wave: dict[str, Any]) -> bool:
    by_id = engine.items_by_id(paths)
    for mem in wave.get("members", []):
        item = by_id.get(mem["work_item_id"])
        if item is None or item["status"] not in ("committed", "cancelled"):
            return False
    return True


def _set_status(paths: Paths, wave: dict[str, Any], status: str, round: int | None = None) -> dict[str, Any]:
    new = dict(wave)
    new["status"] = status
    if round is not None:
        new["round"] = round
    return _append_wave(paths, new)


# --- merge + critic + verdict ----------------------------------------------


def _collect_member_results(paths: Paths, wave: dict[str, Any]) -> list[dict[str, Any]]:
    """Read each COMMITTED member's result file, in wave-member order. Cancelled
    (superseded) members contribute nothing."""
    by_id = engine.items_by_id(paths)
    results: list[dict[str, Any]] = []
    for mem in wave.get("members", []):
        item = by_id.get(mem["work_item_id"])
        if item is None or item["status"] != "committed":
            continue
        p = paths.project_dir / item["output_files"][0]
        if p.exists():
            results.append(json.loads(p.read_text(encoding="utf-8")))
    return results


def merged_relpath(request_id: str) -> str:
    return f"{MERGED_DIR}/{request_id}.merged.json"


def merge(paths: Paths, wave_id: str) -> str:
    """Run the deterministic merger over the wave's terminal members and write
    the ONE merged docs_result.v2 to docs/merged/DR-x.merged.json. Sets status
    to ``merging``. Same member set ⇒ byte-identical file [V-WAVE-02]."""
    wave = wave_by_id(paths, wave_id)
    if wave is None:
        raise DomainError([f"wave not found: {wave_id}"])
    if not _members_terminal(paths, wave):
        raise DomainError([f"wave {wave_id} has non-terminal members; cannot merge"])
    member_results = _collect_member_results(paths, wave)
    merged = merge_results(wave["request_id"], paths.project_id, member_results)
    rel = merged_relpath(wave["request_id"])
    out = paths.project_dir / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    _set_status(paths, wave, "merging")
    return rel


def open_critic(paths: Paths, wave_id: str, actor: str | None = None) -> dict[str, Any]:
    """Dispatch the fresh, adversarial, READ-ONLY coverage critic as a bounded
    worker (its own critic_queue item). It reads the claim/plans/merged
    result/query_logs and fills coverage_report.v1; code computes the verdict."""
    actor = actor or clock_actor()
    wave = wave_by_id(paths, wave_id)
    if wave is None:
        raise DomainError([f"wave not found: {wave_id}"])
    output = f"{COVERAGE_DIR}/{wave_id}.r{wave['round']}.coverage_report.json"
    item = engine.enqueue(paths, queue_name=CRITIC_QUEUE, target_type="wave", target_id=wave_id,
                          task_id=None, output_files=[output], actor=actor)
    _set_status(paths, wave, "critic")
    return item


def resolve_critic(paths: Paths, wave_id: str, critic_wi_id: str, actor: str | None = None) -> dict[str, Any]:
    """Validate the critic's coverage_report (V-WAVE-03), compute the wave
    verdict (CODE — docs/15), and route:
      sufficient / closed → ingest the merged result (one DRES) + status=closed
      followup            → open one member per no_attempt angle + per
                            expected_source, round += 1, status=followup.
    """
    from ..validate.rules import v_path, v_wave

    actor = actor or clock_actor()
    wave = wave_by_id(paths, wave_id)
    if wave is None:
        raise DomainError([f"wave not found: {wave_id}"])
    wi = engine.get_item(paths, critic_wi_id)
    if wi["status"] in ("claimed", "running"):
        wi = engine.complete(paths, critic_wi_id, actor)
    elif wi["status"] != "validating":
        raise DomainError([f"critic item not in validating state: {critic_wi_id} ({wi['status']})"])

    relpath = wi["output_files"][0]
    p = paths.project_dir / relpath
    raw = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    failures = list(v_path.check_output_path(relpath, wi.get("output_files", [])))
    failures += v_path.check_path_safety(paths.project_dir, relpath)
    failures += v_path.check_utf8_json(paths.project_dir, relpath)
    mandatory = tuple(m["angle"] for m in wave["members"] if m["round"] == 1)
    failures += v_wave.check_critic(raw, mandatory=mandatory)
    if failures:
        from ..validate.envelope import to_envelope

        env = to_envelope(failures)
        engine.validate_fail(paths, critic_wi_id, env["failed_rules"], actor, detail=env["detail"])
        raise DomainError(env["failed_rules"], data={"failed_rules": env["failed_rules"], "detail": env["detail"]})

    engine.validate_pass(paths, critic_wi_id, actor, detail={"wave_id": wave_id})
    engine.commit_item(paths, critic_wi_id, actor)

    form = raw.get("form", {})
    expected_sources = raw.get("expected_sources", []) or []
    verdict = wave_verdict(form, wave["round"], mandatory=mandatory)
    specs = followup_specs(form, expected_sources, mandatory=mandatory) if verdict == "followup" else []

    # F2/D2: a followup verdict with an EMPTY follow-up spec list has nothing to
    # open — close the wave immediately rather than spinning an idle round.
    if verdict in ("sufficient", "closed") or (verdict == "followup" and not specs):
        rel = merged_relpath(wave["request_id"])
        ing = ingest.ingest_merged(paths, wave["request_id"], rel, actor)
        _set_status(paths, wave, "closed")
        return {"verdict": verdict, "wave_id": wave_id, "status": "closed",
                "dres_id": ing["dres_id"], "assigned_evidence_ids": ing["assigned_evidence_ids"]}

    # followup: open one member per no_attempt angle + per expected_source.
    next_round = wave["round"] + 1
    new_members = list(wave["members"])
    for spec in specs:
        new_members.append(
            _open_member(paths, wave["request_id"], spec["angle"], next_round,
                         spec["origin"], spec.get("hint"), actor)
        )
    new_wave = dict(wave)
    new_wave["members"] = new_members
    new_wave["round"] = next_round
    new_wave["status"] = "followup"
    _append_wave(paths, new_wave)
    return {"verdict": verdict, "wave_id": wave_id, "status": "followup",
            "round": next_round, "opened": len(specs)}


# --- the production wave drivers (F2/D2: the CLI owns the lifecycle) ---------


def _check_declared_path(paths: Paths, wi: dict[str, Any], file_path: str) -> str:
    """V-PATH-01 at the CLI boundary: the passed file must be the item's declared
    output. Returns the declared relpath used downstream."""
    from .ingest import _to_relpath

    relpath = _to_relpath(paths, file_path)
    declared = list(wi.get("output_files") or [])
    if declared and relpath != declared[0]:
        raise DomainError([f"V-PATH-01: path {relpath} != declared {declared[0]}"],
                          data={"failed_rules": ["V-PATH-01"]})
    return relpath


def wave_member_ingest(paths: Paths, output_file: str, wi_id: str, actor: str | None = None) -> dict[str, Any]:
    """`docs wave-member <output_file> --work-item <WI>` (F2/D2): the ONLY lawful
    completion path for a wave-member docs item. Implicit-complete from
    claimed/running, validate against the member's OWN plan, commit WITHOUT
    ingesting [V-WAVE-05] — and when every member of the wave is terminal,
    AUTO-run the deterministic merge and dispatch the coverage critic in the
    same command."""
    actor = actor or clock_actor()
    wi = engine.get_item(paths, wi_id)
    wave = wave_for_member(paths, wi_id)
    if wave is None:
        raise DomainError([f"work item {wi_id} is not a wave member; use `docs ingest-result`"])
    _check_declared_path(paths, wi, output_file)
    out = complete_member(paths, wave["wave_id"], wi_id, actor)

    wave = wave_by_id(paths, wave["wave_id"])
    if _members_terminal(paths, wave):
        merged_rel = merge(paths, wave["wave_id"])
        critic_item = open_critic(paths, wave["wave_id"], actor)
        out.update({"merged": merged_rel, "critic_work_item_id": critic_item["work_item_id"],
                    "wave_status": "critic"})
    else:
        out["wave_status"] = wave.get("status")
    return out


def wave_resolve(paths: Paths, coverage_report_file: str, wi_id: str, actor: str | None = None) -> dict[str, Any]:
    """`docs wave-resolve <coverage_report_file> --work-item <WI>` (F2/D2):
    V-WAVE-03-validate the critic's report, implicit-complete the critic item,
    and let CODE compute + route the wave verdict (close-and-ingest ONE DRES, or
    open the bounded follow-up round)."""
    actor = actor or clock_actor()
    wi = engine.get_item(paths, wi_id)
    if wi.get("queue_name") != CRITIC_QUEUE:
        raise DomainError([f"work item {wi_id} is not a critic item"])
    _check_declared_path(paths, wi, coverage_report_file)
    return resolve_critic(paths, wi["target_id"], wi_id, actor)
