"""Mechanical scoring for the three-mode ablation. Uniform, objective metrics
across raw / skills / tree: article length, citation count + distinct sources,
source traceability (does every citation map to a saved non-empty source?),
adversarial-section presence, and cited-source total bytes (a floor on the raw
text the mode had to handle). Quote fidelity for the tree mode is separately
guaranteed by `nd check` (verbatim-verified archive)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CJK = re.compile(r"[a-z0-9]+|[一-鿿]")
S_CITE = re.compile(r"\(S(\d+)\)")
DOC_CITE = re.compile(r"\(cite:\s*(DOC-\d{4})\)")
ADVERSARIAL = ("反", "对立", "对抗", "反证", "反方", "局限", "counter", "limitation",
               "discussion", "caveat", "disconfirm")


def wordcount(text: str) -> int:
    return len(CJK.findall(text.lower()))


def score_run(run: Path, mode: str) -> dict:
    article = run / "article.md"
    if not article.is_file():
        return {"mode": mode, "error": "no article.md"}
    text = article.read_text(encoding="utf-8", errors="replace")

    if mode == "tree":
        cites = DOC_CITE.findall(text)
        distinct = sorted(set(cites))
        store = run / "sessions" / "cmp" / "docs" / "store"
        def src_for(c): return store / f"{c}.txt"
    else:
        cites = [f"S{n}" for n in S_CITE.findall(text)]
        distinct = sorted(set(cites), key=lambda s: int(s[1:]))
        srcdir = run / "sources"
        def src_for(c): return srcdir / f"{c}.txt"

    traceable = 0
    src_bytes = 0
    for c in distinct:
        f = src_for(c)
        if f.is_file() and f.stat().st_size > 0:
            traceable += 1
            src_bytes += f.stat().st_size

    # references section: strip it from the body wordcount for fairness
    body = re.split(r"#+\s*(References|参考文献|引用)", text)[0]

    return {
        "mode": mode,
        "words": wordcount(body),
        "citations_inline": len(cites),
        "distinct_sources": len(distinct),
        "traceable_sources": traceable,
        "traceability": round(traceable / len(distinct), 3) if distinct else 0.0,
        "cited_source_bytes": src_bytes,
        "has_adversarial_section": any(k in text for k in ADVERSARIAL),
        "adversarial_hits": sum(text.count(k) for k in ADVERSARIAL),
    }


def main(base: str) -> None:
    base = Path(base)
    out = []
    for mode in ("raw", "skills", "tree"):
        out.append(score_run(base / "runs" / mode, mode))
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
