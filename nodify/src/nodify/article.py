"""V3 article layer: the tree rendered into an auditable paper.

The model decides everything editorial (what to include, structure, prose);
the framework records the decisions and enforces traceability: an outline must
ground its thesis in existing syntheses, every `(cite: DOC-xxxx)` in prose
must resolve to an archived docs entry, and assemble emits the references
section mechanically from the cites actually present."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import docsdb, store, tree
from .clock import now as clock_now
from .errors import DomainError, UsageError
from .paths import Paths
from .schemas import validate

RECORDS = "article/records.jsonl"
OUTLINE_ID = "OL-01"
CITE_RE = re.compile(r"\(cite:\s*(DOC-\d{4})\)")
SEC_RE = re.compile(r"^S-\d{2}$")


def records(paths: Paths) -> list[dict[str, Any]]:
    return store.read_all(paths.resolve(RECORDS))


def latest_outline(paths: Paths) -> dict[str, Any] | None:
    found = None
    for rec in records(paths):
        if rec["schema"] == "article.outline.v1":
            found = rec
    return found


def latest_sections(paths: Paths) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rec in records(paths):
        if rec["schema"] == "article.section.v1":
            out[rec["section_id"]] = rec
    return out


def set_outline(paths: Paths, payload: dict[str, Any]) -> dict[str, Any]:
    """payload = article.outline.v1 minus schema/outline_id/created_at."""
    nodes = tree.nodes_by_id(paths)
    syn_ids = {s["synthesis_id"] for s in tree.syntheses(paths)}
    for sid in payload.get("grounded_in", []):
        if sid not in syn_ids:
            raise DomainError([f"grounded_in references unknown synthesis: {sid}"])
    for sec in payload.get("sections", []):
        for nid in sec.get("node_ids", []):
            if nid not in nodes:
                raise DomainError([f"section {sec.get('section_id')} references "
                                   f"unknown node: {nid}"])
    for ex in payload.get("excluded", []):
        if ex.get("node_id") not in nodes:
            raise DomainError([f"excluded references unknown node: {ex.get('node_id')}"])
    record = {"schema": "article.outline.v1", "outline_id": OUTLINE_ID,
              **{k: payload.get(k) for k in
                 ("title", "thesis", "grounded_in", "sections")},
              "excluded": payload.get("excluded", []),
              "created_at": clock_now()}
    errs = validate(record)
    if errs:
        raise DomainError(errs)
    store.append(paths.resolve(RECORDS), record)
    return record


def register_section(paths: Paths, section_id: str, draft: Path
                     ) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if not SEC_RE.match(section_id):
        raise UsageError([f"section id must look like S-01, got {section_id!r}"])
    if not draft.is_file():
        raise UsageError([f"draft file not found: {draft}"])
    outline = latest_outline(paths)
    if outline is None:
        raise DomainError(["no outline yet — nd article outline first"])
    known = {s["section_id"] for s in outline["sections"]}
    if section_id not in known:
        warnings.append(f"{section_id} is not in the latest outline "
                        f"({sorted(known)}) — registered anyway")
    text = draft.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        raise DomainError(["draft is empty"])
    cites = sorted(set(CITE_RE.findall(text)))
    entries = docsdb.entries_by_id(paths)
    dangling = [c for c in cites if c not in entries]
    if dangling:
        raise DomainError([f"cite does not resolve to an archived doc: {c}"
                           for c in dangling])
    if text.lstrip().startswith("#"):
        warnings.append(f"{section_id}: draft starts with a markdown heading — "
                        "assemble adds section headings itself; remove yours "
                        "or they will double")
    role = next((s["role"] for s in outline["sections"]
                 if s["section_id"] == section_id), None)
    if not cites and role in (None, "argument", "evidence"):
        warnings.append(f"{section_id} cites nothing")
    dest_rel = f"article/{section_id}.md"
    dest = paths.resolve(dest_rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    record = {"schema": "article.section.v1", "section_id": section_id,
              "source_file": str(draft), "file": dest_rel, "cites": cites,
              "word_count": len(docsdb._TOKEN.findall(text.lower())),
              "created_at": clock_now()}
    errs = validate(record)
    if errs:
        raise DomainError(errs)
    store.append(paths.resolve(RECORDS), record)
    return record, warnings


FINAL = "article/final.md"


def _render(paths: Paths) -> tuple[str, dict[str, Any], list[str]]:
    """Deterministic assembly of the final article TEXT from the latest outline
    + registered sections. Pure: no disk write. `assemble` writes what this
    returns; `check` recomputes it to detect a stale final.md (R1)."""
    warnings: list[str] = []
    outline = latest_outline(paths)
    if outline is None:
        raise DomainError(["no outline yet — nd article outline first"])
    sections = latest_sections(paths)
    entries = docsdb.entries_by_id(paths)

    parts = [f"# {outline['title']}", "", f"> {outline['thesis']}", ""]
    all_cites: list[str] = []
    missing = []
    for sec in outline["sections"]:
        sid = sec["section_id"]
        rec = sections.get(sid)
        if rec is None or not paths.resolve(rec["file"]).is_file():
            missing.append(sid)
            continue
        text = paths.resolve(rec["file"]).read_text(encoding="utf-8",
                                                    errors="replace")
        parts += [f"## {sec['title']}", "", text.strip(), ""]
        all_cites += rec["cites"]
    if missing:
        warnings.append(f"sections without registered prose, skipped: {missing}")

    cited = sorted(set(all_cites))
    if cited:
        parts += ["## References", ""]
        for doc_id in cited:
            e = entries.get(doc_id)
            if e is None:  # register_section guards this; belt and braces
                raise DomainError([f"cite does not resolve: {doc_id}"])
            src = e["url"] or e["text_file"]
            parts.append(f"- [{doc_id}] {e['title']} — {src}")
        parts.append("")
    text = "\n".join(parts)
    meta = {"file": FINAL,
            "sections": [s["section_id"] for s in outline["sections"]
                         if s["section_id"] in sections
                         and paths.resolve(sections[s["section_id"]]["file"]).is_file()],
            "skipped": missing, "references": cited}
    return text, meta, warnings


def assemble(paths: Paths) -> tuple[dict[str, Any], list[str]]:
    text, meta, warnings = _render(paths)
    paths.resolve(FINAL).write_text(text, encoding="utf-8")
    return meta, warnings


def check(paths: Paths, nodes: dict[str, Any], syn_ids: set[str],
          entries: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Article-layer additions for nd check (only when records exist)."""
    hard: list[str] = []
    soft: list[str] = []
    recs = records(paths)
    if not recs:
        return hard, soft
    for rec in recs:
        hard += validate(rec)
    outline = latest_outline(paths)
    sections = latest_sections(paths)
    if outline:
        for sid in outline["grounded_in"]:
            if sid not in syn_ids:
                hard.append(f"outline grounded_in dangling synthesis: {sid}")
        for sec in outline["sections"]:
            for nid in sec["node_ids"]:
                if nid not in nodes:
                    hard.append(f"outline section {sec['section_id']} dangling node: {nid}")
            if sec["section_id"] not in sections:
                soft.append(f"outline section {sec['section_id']} has no registered prose")
            elif sec["role"] in ("argument", "evidence") \
                    and not sections[sec['section_id']]["cites"]:
                soft.append(f"{sec['section_id']} ({sec['role']}) cites nothing")
        known = {s["section_id"] for s in outline["sections"]}
        for sid in sections:
            if sid not in known:
                soft.append(f"registered section {sid} is not in the latest outline")
    for rec in sections.values():
        if not paths.resolve(rec["file"]).is_file():
            hard.append(f"{rec['section_id']}: prose file missing: {rec['file']}")
            continue
        text = paths.resolve(rec["file"]).read_text(encoding="utf-8",
                                                    errors="replace")
        for c in set(CITE_RE.findall(text)):
            if c not in entries:
                hard.append(f"{rec['section_id']}: cite does not resolve: {c}")

    # R1 (P2 fix): a final.md on disk must equal what the current outline +
    # registered sections would assemble to — otherwise it is stale. Only run
    # this once the article is structurally sound (no missing files / dangling
    # cites above), so the byte comparison is meaningful.
    final = paths.resolve(FINAL)
    if not hard and outline is not None and final.is_file():
        try:
            expected, _, _ = _render(paths)
        except DomainError:
            expected = None
        if expected is not None and \
                final.read_text(encoding="utf-8", errors="replace") != expected:
            hard.append("article/final.md is stale — the outline or a section "
                        "changed since assembly; re-run nd article assemble")
    return hard, soft
