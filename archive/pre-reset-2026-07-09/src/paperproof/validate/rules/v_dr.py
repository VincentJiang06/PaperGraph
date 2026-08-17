"""V-DR: docs-result validation (docs/04, docs/08 B7, docs/09).

The DocsWorker submits a DocsResult (documents + evidence units, no ids); the
ingestor assigns DOC-/EU-/DRES- ids. V-DR validates the result before any state
is written.

Check order mirrors V-PR: the caller runs V-PATH first, then this module's
``raw_scan`` (V-DR-03) BEFORE schema parsing, then ``check`` (schema V-DR-01, then
the semantic rules). V-DR-05 (quote substring) is a per-EU check against the
archived text and so is evaluated at ingest, when the text exists.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from ...schemas.docs import DocsResult, DocsResultV2
from ...textutil import quote_match
from ..envelope import Failure

_SOURCE_TYPES = {
    "peer_reviewed", "official_report", "working_paper", "news", "dataset", "user_notes"
}

# Fields a DocsResult legitimately carries. request_id is top-level; doc_id is an
# EU's reference to an EXISTING archived document (V-DR-01). Any other id-valued
# field, or a verdict/strength/lifecycle field, is worker overreach (V-DR-03).
_ALLOWED_ID_KEYS = {"doc_id", "request_id", "project_id"}
_FORBIDDEN_KEYS = {"verdict", "strength", "lifecycle", "lifecycle_state"}


# --- V-DR-03 raw scan (runs before schema parse) ---------------------------


def raw_scan(raw: Any) -> list[Failure]:
    """V-DR-03: no verdict/strength/lifecycle field anywhere; no worker-authored
    id field beyond the schema's own (ingestor assigns DOC-/EU-/DRES- ids)."""
    failures: list[Failure] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in _FORBIDDEN_KEYS:
                    failures.append(Failure("V-DR-03", f"forbidden field {key!r} at {path}"))
                if key.endswith("_id") and key not in _ALLOWED_ID_KEYS:
                    failures.append(Failure("V-DR-03", f"worker-authored id field {key!r} at {path}"))
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")

    walk(raw, "$")
    return failures


# --- V-DR-01 + semantic rules ----------------------------------------------


def check(
    result_dict: dict[str, Any],
    *,
    archived_doc_ids: set[str] | None = None,
    archived_texts: dict[str, str] | None = None,
) -> list[Failure]:
    """Validate a DocsResult (V-DR-01..06).

    ``archived_doc_ids`` resolves an EU's ``doc_id`` reference (V-DR-01);
    ``archived_texts`` maps an existing doc_id -> its archived text for the
    V-DR-05 quote check (inline text is used for ``doc_ref`` web documents).
    """
    archived_doc_ids = archived_doc_ids or set()
    archived_texts = archived_texts or {}

    # V-DR-01: schema parse. docs_result.v2 carries a structured query_log in
    # place of v1's free-string search_log; both share every other field, so the
    # V-DR-02/04/05 checks below are version-agnostic (docs/14).
    is_v2 = result_dict.get("schema_version") == "docs_result.v2"
    model = DocsResultV2 if is_v2 else DocsResult
    try:
        result = model.model_validate(result_dict)
    except ValidationError as exc:
        return [Failure("V-DR-01", f"schema invalid: {exc.errors()[:2]}")]

    failures: list[Failure] = []
    documents = result.documents
    n_docs = len(documents)

    # V-DR-06: not_found terminal shape. The activity log that must be non-empty
    # is search_log (v1) or query_log (v2) — re-expressed per docs/14 adoption.
    if result.not_found:
        if documents or result.evidence_units:
            failures.append(Failure("V-DR-06", "not_found=true requires empty documents + evidence_units"))
        activity_log = result.query_log if is_v2 else result.search_log
        if not activity_log:
            log_name = "query_log" if is_v2 else "search_log"
            failures.append(Failure("V-DR-06", f"not_found=true requires a non-empty {log_name}"))

    # V-DR-04: document source_type + origin; web documents include inline text.
    for i, doc in enumerate(documents):
        if doc.source_type not in _SOURCE_TYPES:
            failures.append(Failure("V-DR-04", f"documents[{i}] bad source_type {doc.source_type!r}"))
        kind = doc.origin.kind
        if kind == "user_provided" and not doc.origin.path:
            failures.append(Failure("V-DR-04", f"documents[{i}] user_provided origin needs a path"))
        if kind == "web":
            if not doc.origin.url:
                failures.append(Failure("V-DR-04", f"documents[{i}] web origin needs a url"))
            if not (doc.text and doc.text.strip()):
                failures.append(Failure("V-DR-04", f"documents[{i}] web document needs inline text"))

    # per-EvidenceUnit rules.
    for j, eu in enumerate(result.evidence_units):
        # V-DR-01: exactly one of doc_ref / doc_id, and it resolves.
        has_ref = eu.doc_ref is not None
        has_id = eu.doc_id is not None
        if has_ref == has_id:
            failures.append(Failure("V-DR-01", f"evidence_units[{j}] needs exactly one of doc_ref/doc_id"))
        elif has_ref:
            if not (0 <= eu.doc_ref < n_docs):
                failures.append(Failure("V-DR-01", f"evidence_units[{j}] doc_ref {eu.doc_ref} out of range"))
        else:
            if eu.doc_id not in archived_doc_ids:
                failures.append(Failure("V-DR-01", f"evidence_units[{j}] doc_id {eu.doc_id!r} not archived"))

        # V-DR-02: both citation-boundary lists non-empty.
        if not eu.can_cite_for or not eu.cannot_cite_for:
            failures.append(Failure("V-DR-02", f"evidence_units[{j}] needs non-empty can/cannot_cite_for"))

        # V-DR-05: quote must appear verbatim in the archived text (when text exists).
        if eu.kind == "quote":
            text = None
            if has_ref and 0 <= (eu.doc_ref or 0) < n_docs:
                text = documents[eu.doc_ref].text
            elif has_id:
                text = archived_texts.get(eu.doc_id)
            if text:  # rule applies iff the document has text
                if not quote_match(text, eu.quote_or_paraphrase):
                    failures.append(Failure("V-DR-05", f"evidence_units[{j}] quote not found in archived text"))

    return failures
