"""Blind the two investigation dossiers per topic for the judge panel. Dossiers list
evidence as `title — url — "quote"` (no numbered inline cites), so blinding is mostly:
(1) assign A/B slots per topic with a per-topic rotation (kill position bias),
(2) scrub any residual arm tells (tree node-ids / nd jargon; dossier.py already emits
neutral L-labels, this is belt-and-suspenders). Evidence provenance is preserved —
that's real quality signal; the judge never learns the arms exist.

Usage: python3 blind.py <base>   # base has runs/<topic>/{tree,notree}/dossier.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ARMS = ("tree", "notree")
# residual arm tells to neutralize. NO \b anchors — ids are frequently glued to CJK
# text in author-written summaries (e.g. "见N-0013"), where \b fails to match.
NODE_REF = re.compile(r"(?:见|参见|呼应|如|见\s*)?(?:N-\d{4})(?:\s*[/、,，]\s*N-\d{4})*")
JARGON = re.compile(r"(SYN-\d{4}|DOC-\d{4}|nd check|nd article|nd export|nd brief|"
                    r"logic tree|synthesis record|nodify)", re.I)


def scrub(text: str) -> str:
    text = NODE_REF.sub("〔另一分支〕", text)   # cross-refs between tree nodes
    text = JARGON.sub("(记录)", text)
    return text


def topics(base: Path):
    return sorted(d.name for d in (base / "runs").glob("*")
                  if (d / "tree" / "dossier.md").is_file() or (d / "notree" / "dossier.md").is_file())


def slot_map(topic_list):
    """Alternate which arm is slot A across topics (deterministic)."""
    m = {}
    for i, t in enumerate(topic_list):
        m[t] = {"A": "tree", "B": "notree"} if i % 2 == 0 else {"A": "notree", "B": "tree"}
    return m


def main(base: str = "."):
    base = Path(base)
    tlist = topics(base)
    slots = slot_map(tlist)
    outdir = base / "blinded"
    key = {}
    for t in tlist:
        (outdir / t).mkdir(parents=True, exist_ok=True)
        key[t] = {}
        for slot, arm in slots[t].items():
            d = base / "runs" / t / arm / "dossier.md"
            if not d.is_file():
                key[t][slot] = f"{arm} (MISSING)"
                continue
            (outdir / t / f"dossier-{slot}.md").write_text(scrub(d.read_text(encoding="utf-8")), encoding="utf-8")
            key[t][slot] = arm
    (outdir / "KEY.json").write_text(json.dumps(key, ensure_ascii=False, indent=2))
    print("blinded ->", outdir)
    print(json.dumps(key, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
