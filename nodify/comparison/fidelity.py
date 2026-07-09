"""Quote-fidelity check: of the English verbatim quotes an article claims, how
many actually appear (whitespace-normalized) in that mode's saved sources? This
is the anti-hallucination metric. The tree mode's quotes are already verbatim-
verified by `nd check`; this runs the SAME test uniformly on all three so the
numbers are comparable. Chinese 'quotes' are skipped — they are usually
translations (not checkable as verbatim)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# quoted spans: straight/curly double quotes and CJK quote brackets
QUOTE = re.compile(r"[\"“「『]([^\"”」』]{12,400})"
                   r"[\"”」』]")
LATIN_RUN = re.compile(r"[A-Za-z]{2,}")
WS = re.compile(r"\s+")
PUNCT = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                       "–": "-", "—": "-", " ": " ", "…": "..."})


def norm(s: str) -> str:
    return WS.sub(" ", s.translate(PUNCT)).strip().lower()


def english_quotes(text: str) -> list[str]:
    out = []
    for m in QUOTE.findall(text):
        # keep quotes that are substantially English (>= 5 latin word runs)
        if len(LATIN_RUN.findall(m)) >= 5:
            out.append(m)
    return out


def sources_blob(mode: str, run: Path) -> str:
    if mode == "tree":
        d = run / "sessions" / "cmp" / "docs" / "store"
        files = sorted(d.glob("*.txt")) if d.is_dir() else []
    else:
        d = run / "sources"
        files = sorted(d.glob("*.txt")) if d.is_dir() else []
    return norm(" ".join(f.read_text(encoding="utf-8", errors="replace") for f in files))


def check(mode: str, run: Path) -> dict:
    art = run / "article.md"
    if not art.is_file():
        return {"mode": mode, "error": "no article"}
    quotes = english_quotes(art.read_text(encoding="utf-8", errors="replace"))
    blob = sources_blob(mode, run)
    found = [q for q in quotes if norm(q) in blob]
    missing = [q for q in quotes if norm(q) not in blob]
    return {
        "mode": mode,
        "english_quotes": len(quotes),
        "verbatim_in_sources": len(found),
        "fidelity": round(len(found) / len(quotes), 3) if quotes else None,
        "unverified_examples": [q[:80] for q in missing[:4]],
    }


def main(base: str) -> None:
    base = Path(base)
    out = [check(m, base / "runs" / m) for m in ("raw", "skills", "tree")]
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
