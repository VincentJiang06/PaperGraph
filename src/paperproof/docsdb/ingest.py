"""The Docs ingestor (docs/04, docs/08 B7): the ONLY writer of docs/*.jsonl +
docs/raw + docs/text.

Two entry points:
  ingest_file    `docs ingest` — a user file -> a Document (dedup by content_hash).
  ingest_result  `docs ingest-result` — a validated DocsResult -> Documents +
                 EvidenceUnits, the DocsRequest status update, and the re-proof
                 unblock. Ids (DOC-/EU-/DRES-) are assigned here; the worker
                 authors none.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from ..clock import actor as clock_actor
from ..clock import now as clock_now
from ..errors import DomainError, UsageError
from ..ids import next_id
from ..paths import Paths
from ..queue import engine
from ..schemas.docs import DocsResult, Document, EvidenceUnit
from ..store import jsonl
from ..validate.envelope import Failure, to_envelope
from ..validate.rules import v_dr, v_path

DOCUMENTS = "docs/documents.jsonl"
EVIDENCE_UNITS = "docs/evidence_units.jsonl"
DOCS_REQUESTS = "docs/docs_requests.jsonl"

_DRES_RE = re.compile(r"^DRES-\d+$")


def _sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _unique_citation_key(candidate: str, existing: set[str]) -> str:
    """Citation keys are unique across the project; the ingestor appends -b, -c
    (then -d ...) on collision (docs/04)."""
    if candidate not in existing:
        return candidate
    suffix = ord("b")
    while f"{candidate}-{chr(suffix)}" in existing:
        suffix += 1
    return f"{candidate}-{chr(suffix)}"


# --- `docs ingest`: user file -> Document -----------------------------------


def ingest_file(
    paths: Paths,
    file_path: str,
    source_type: str | None = None,
    title: str | None = None,
    citation_key: str | None = None,
) -> dict[str, Any]:
    """Archive a user-provided file as a Document. content_hash = sha256 of the
    raw bytes is the dedup key: the same content twice returns the existing
    doc_id and appends no new record."""
    src = Path(file_path)
    if not src.exists():
        raise UsageError([f"file not found: {file_path}"])
    raw = src.read_bytes()
    content_hash = _sha(raw)
    warnings: list[str] = []

    existing = jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")
    for d in existing:
        if d.get("content_hash") == content_hash:
            return {"doc_id": d["doc_id"], "text_path": d.get("text_path"),
                    "deduped": True, "warnings": [f"content already archived as {d['doc_id']}"]}

    doc_id = next_id("DOC", [d["doc_id"] for d in existing])
    ext = src.suffix.lower()
    raw_rel = f"docs/raw/{doc_id}{ext or '.bin'}"
    raw_dst = paths.resolve(raw_rel)
    raw_dst.parent.mkdir(parents=True, exist_ok=True)
    raw_dst.write_bytes(raw)

    # text extraction: .txt/.md verbatim; .pdf via pypdf; else / failure -> null.
    text_rel: str | None = None
    if ext in (".txt", ".md"):
        text = raw.decode("utf-8", errors="replace")
        text_rel = f"docs/text/{doc_id}.txt"
        paths.resolve(text_rel).write_text(text, encoding="utf-8")
    elif ext == ".pdf":
        text = _extract_pdf_text(raw_dst)
        if text is None:
            warnings.append(f"pdf text extraction failed for {doc_id}; text_path=null")
        else:
            text_rel = f"docs/text/{doc_id}.txt"
            paths.resolve(text_rel).write_text(text, encoding="utf-8")
    else:
        warnings.append(f"no text extractor for {ext!r}; text_path=null")

    existing_keys = {d["citation_key"] for d in existing}
    ck = _unique_citation_key(citation_key or src.stem, existing_keys)
    record = Document(
        doc_id=doc_id, project_id=paths.project_id, title=title or src.stem,
        source_type=source_type or "user_notes",
        origin={"kind": "user_provided", "path": raw_rel, "url": None},
        content_hash=content_hash, text_path=text_rel, citation_key=ck,
        ingested_from=None, ingested_at=clock_now(),
    )
    jsonl.append(paths.resolve(DOCUMENTS), record)
    return {"doc_id": doc_id, "text_path": text_rel, "citation_key": ck, "deduped": False, "warnings": warnings}


def _extract_pdf_text(pdf_path: Path) -> str | None:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        parts = [(page.extract_text() or "") for page in reader.pages]
        text = "\n".join(parts).strip()
        return text or None
    except Exception:
        return None


# --- `docs ingest-result`: DocsResult -> Documents + EvidenceUnits ----------


def _next_dres_id(paths: Paths) -> str:
    seen: set[str] = set()
    for rel, field in ((DOCUMENTS, "ingested_from"), (EVIDENCE_UNITS, "ingested_from"),
                       (DOCS_REQUESTS, "fulfilled_by")):
        for r in jsonl.read_all(paths.resolve(rel)):
            v = r.get(field)
            if isinstance(v, str) and _DRES_RE.match(v):
                seen.add(v)
    return next_id("DRES", seen)


def _validate(paths: Paths, wi: dict[str, Any], relpath: str, raw: dict[str, Any]) -> list[Failure]:
    """V-PATH + V-DR (schema V-DR-01, raw V-DR-03, semantic V-DR-02/04/05/06)."""
    failures: list[Failure] = []
    failures += v_path.check_output_path(relpath, wi.get("output_files", []))
    failures += v_path.check_path_safety(paths.project_dir, relpath)
    vpath03 = v_path.check_utf8_json(paths.project_dir, relpath)
    failures += vpath03
    lease = wi.get("lease") or {}
    if lease.get("manifest"):
        failures += v_path.check_lease_scan(paths.project_dir, lease["manifest"])
    if vpath03:
        return failures
    failures += v_dr.raw_scan(raw)
    existing = jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")
    archived_ids = {d["doc_id"] for d in existing}
    archived_texts: dict[str, str] = {}
    for d in existing:
        tp = d.get("text_path")
        if tp:
            p = paths.resolve(tp)
            if p.exists():
                archived_texts[d["doc_id"]] = p.read_text(encoding="utf-8")
    failures += v_dr.check(raw, archived_doc_ids=archived_ids, archived_texts=archived_texts)
    return failures


def ingest_result(paths: Paths, output_file: str, work_item_id: str, actor: str | None = None) -> dict[str, Any]:
    actor = actor or clock_actor()
    wi = engine.get_item(paths, work_item_id)
    # r3 (docs/05 §Validation Gate): the docs validate-and-ingest path likewise
    # completes an item still in claimed/running itself, against its claim-time
    # lease manifest, so no separate `queue complete` call is required.
    if wi["status"] in ("claimed", "running"):
        wi = engine.complete(paths, work_item_id, actor)
    elif wi["status"] != "validating":
        raise DomainError([f"docs work item not in validating state: {work_item_id} ({wi['status']})"])
    relpath = _to_relpath(paths, output_file)

    raw = json.loads((paths.project_dir / relpath).read_text(encoding="utf-8")) if (paths.project_dir / relpath).exists() else {}
    failures = _validate(paths, wi, relpath, raw)
    if failures:
        env = to_envelope(failures)
        engine.validate_fail(paths, work_item_id, env["failed_rules"], actor, detail=env["detail"])
        raise DomainError(env["failed_rules"], data={"failed_rules": env["failed_rules"], "detail": env["detail"]})

    result = DocsResult.model_validate(raw)
    dres_id = _next_dres_id(paths)
    extracted_by = (wi.get("lease") or {}).get("claimed_by") or "docs-worker"

    existing_docs = jsonl.latest_records(paths.resolve(DOCUMENTS), "doc_id")
    hash_to_id = {d["content_hash"]: d["doc_id"] for d in existing_docs}
    existing_doc_ids = [d["doc_id"] for d in existing_docs]
    existing_keys = {d["citation_key"] for d in existing_docs}

    assigned_docs: list[str] = []
    doc_index_to_id: dict[int, str] = {}
    for i, doc in enumerate(result.documents):
        text = doc.text or ""
        content_hash = _sha(text.encode("utf-8"))
        if content_hash in hash_to_id:  # dedup by content_hash
            doc_index_to_id[i] = hash_to_id[content_hash]
            continue
        doc_id = next_id("DOC", existing_doc_ids)
        existing_doc_ids.append(doc_id)
        raw_rel = f"docs/raw/{doc_id}.txt"
        paths.resolve(raw_rel).parent.mkdir(parents=True, exist_ok=True)
        paths.resolve(raw_rel).write_text(text, encoding="utf-8")
        # text_path is null when no text could be extracted (docs/04); do not
        # write an empty text file, mirroring the `docs ingest` path.
        text_rel: str | None = None
        if text:
            text_rel = f"docs/text/{doc_id}.txt"
            paths.resolve(text_rel).parent.mkdir(parents=True, exist_ok=True)
            paths.resolve(text_rel).write_text(text, encoding="utf-8")
        ck = _unique_citation_key(doc.citation_key, existing_keys)
        existing_keys.add(ck)
        record = Document(
            doc_id=doc_id, project_id=paths.project_id, title=doc.title,
            source_type=doc.source_type, origin=doc.origin, content_hash=content_hash,
            text_path=text_rel, citation_key=ck, ingested_from=dres_id, ingested_at=clock_now(),
        )
        jsonl.append(paths.resolve(DOCUMENTS), record)
        hash_to_id[content_hash] = doc_id
        doc_index_to_id[i] = doc_id
        assigned_docs.append(doc_id)

    existing_eu_ids = [e["evidence_id"] for e in jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")]
    assigned_eus: list[str] = []
    for eu in result.evidence_units:
        doc_id = doc_index_to_id[eu.doc_ref] if eu.doc_ref is not None else eu.doc_id
        eid = next_id("EU", existing_eu_ids)
        existing_eu_ids.append(eid)
        record = EvidenceUnit(
            evidence_id=eid, project_id=paths.project_id, doc_id=doc_id, location=eu.location,
            kind=eu.kind, quote_or_paraphrase=eu.quote_or_paraphrase, summary=eu.summary,
            support_direction=eu.support_direction, can_cite_for=list(eu.can_cite_for),
            cannot_cite_for=list(eu.cannot_cite_for), scope=eu.scope, extracted_by=extracted_by,
            ingested_from=dres_id, created_at=clock_now(),
        )
        jsonl.append(paths.resolve(EVIDENCE_UNITS), record)
        assigned_eus.append(eid)

    status = "not_found" if result.not_found else "fulfilled"
    _append_request_status(paths, result.request_id, status, dres_id)

    # unblock the waiting re-proof: validated -> committed marks the docs item
    # terminal so its dependent proof item's blockers resolve (docs/08 B7).
    engine.validate_pass(paths, work_item_id, actor, detail={"dres_id": dres_id})
    engine.commit_item(paths, work_item_id, actor)

    # Evidence-arrival staleness (docs/04 r3, V-TASK-04): freshly archived
    # evidence must reach pending proofs without human intervention. Mark stale
    # every queued/blocked PROOF item whose target the new EUs are REQUESTED
    # for or whose matcher output would now change — its next build-tasks run
    # mints a fresh -rN pack. (Live run: a re-proof nearly ran on a 10-EU pack
    # while 24 EUs existed; only a manual build-task rebuilt it.)
    if assigned_eus:
        _mark_stale_on_evidence_arrival(paths, assigned_eus, dres_id, actor)

    return {"dres_id": dres_id, "assigned_doc_ids": assigned_docs, "assigned_evidence_ids": assigned_eus,
            "request_id": result.request_id, "status": status}


def _mark_stale_on_evidence_arrival(paths: Paths, new_eu_ids: list[str], dres_id: str, actor: str) -> None:
    from ..graph import model as graph_model  # local: avoid import cycle
    from . import matcher as _matcher

    new_eus = [
        eu for eu in jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
        if eu["evidence_id"] in set(new_eu_ids)
    ]
    requested_targets = {
        r.get("target_id")
        for r in jsonl.latest_records(paths.resolve(DOCS_REQUESTS), "request_id")
        if r.get("fulfilled_by") == dres_id
    }
    gv = graph_model.load(paths)
    for item in engine.load_items(paths):
        if item.get("queue_name") != "proof_queue" or item.get("status") not in ("queued", "blocked"):
            continue
        tgt_id = item.get("target_id")
        affected = tgt_id in requested_targets
        if not affected:
            rec = gv.node_by_id.get(tgt_id) or gv.edge_by_id.get(tgt_id)
            if rec is not None:
                if "edge_id" in rec:
                    claim, scope = rec.get("edge_claim", "") or "", {}
                else:
                    claim, scope = rec.get("claim", "") or "", rec.get("scope", {}) or {}
                affected = bool(_matcher.match(claim, scope, new_eus))
        if affected:
            engine.invalidate(paths, item["work_item_id"], actor,
                              detail={"reason": "evidence_arrival", "dres_id": dres_id})


def _append_request_status(paths: Paths, request_id: str, status: str, dres_id: str) -> None:
    latest = jsonl.latest_by_id(paths.resolve(DOCS_REQUESTS), "request_id").get(request_id)
    if latest is None:
        raise DomainError([f"docs request not found: {request_id}"])
    new = dict(latest)
    new["status"] = status
    new["fulfilled_by"] = dres_id
    new["created_at"] = clock_now()
    jsonl.append(paths.resolve(DOCS_REQUESTS), new)


def _to_relpath(paths: Paths, output_file: str) -> str:
    p = Path(output_file)
    if p.is_absolute():
        try:
            return str(p.resolve().relative_to(paths.project_dir.resolve()))
        except ValueError:
            return output_file
    return output_file
