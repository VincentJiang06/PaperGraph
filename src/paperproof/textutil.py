"""Shared text algorithms (docs/09 §0).

This module is the ONLY tokenizer/counter/measurer in the system. Every rule
family cites these functions; no other module may improvise its own tokenizer.
Implemented exactly as pinned in docs/09 §0.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# The frozen stopword list, VERBATIM (docs/09 §0). Exactly 82 words.
# Changing this list is a spec change.
STOPWORDS: frozenset[str] = frozenset(
    [
        "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
        "while", "of", "at", "by", "for", "with", "about", "against", "between",
        "into", "through", "during", "before", "after", "above", "below", "to",
        "from", "up", "down", "in", "out", "on", "off", "over", "under", "again",
        "once", "here", "there", "all", "any", "both", "each", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "same",
        "so", "than", "too", "very", "can", "will", "just", "is", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "that", "this", "these", "those", "it", "its", "as",
    ]
)

_WHITESPACE_RE = re.compile(r"\s+")


def normalize(s: str) -> str:
    """NFC -> collapse every whitespace run to one space -> strip."""
    s = unicodedata.normalize("NFC", s)
    s = _WHITESPACE_RE.sub(" ", s)
    return s.strip()


def casefold(s: str) -> str:
    """normalize(s) -> Unicode casefold."""
    return normalize(s).casefold()


def is_cjk(ch: str) -> bool:
    """True iff codepoint is in one of the pinned CJK ranges.

    CJK Unified Ideographs U+4E00-9FFF, Extension A U+3400-4DBF,
    Hiragana/Katakana U+3040-30FF, or Hangul Syllables U+AC00-D7AF.
    """
    if not ch:
        return False
    cp = ord(ch[0])
    return (
        0x4E00 <= cp <= 0x9FFF
        or 0x3400 <= cp <= 0x4DBF
        or 0x3040 <= cp <= 0x30FF
        or 0xAC00 <= cp <= 0xD7AF
    )


def tokens(s: str) -> list[str]:
    """casefold(s) split on non-alphanumeric boundaries; every is_cjk char is
    its own token; empty tokens dropped."""
    folded = casefold(s)
    result: list[str] = []
    buf: list[str] = []
    for ch in folded:
        if is_cjk(ch):
            if buf:
                result.append("".join(buf))
                buf = []
            result.append(ch)
        elif ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                result.append("".join(buf))
                buf = []
    if buf:
        result.append("".join(buf))
    return [t for t in result if t]


def word_count(s: str) -> int:
    """count of tokens(s) - a CJK character counts as one word."""
    return len(tokens(s))


# ASCII sentence terminators split when followed by whitespace or EOL.
# CJK terminators split ALWAYS.
_CJK_TERMINATORS = "。！？"  # 。！？
_ASCII_TERMINATORS = ".!?"


def sentence_split(s: str) -> list[str]:
    """Split into sentences per docs/09 §0.

    ASCII terminators . ! ? split when followed by whitespace or EOL.
    CJK terminators 。！？ split ALWAYS. Trailing fragment counts if non-empty.
    """
    sentences: list[str] = []
    current: list[str] = []
    n = len(s)
    for i, ch in enumerate(s):
        current.append(ch)
        if ch in _CJK_TERMINATORS:
            sentence = "".join(current).strip()
            if sentence:
                sentences.append(sentence)
            current = []
        elif ch in _ASCII_TERMINATORS:
            nxt = s[i + 1] if i + 1 < n else ""
            if nxt == "" or nxt.isspace():
                sentence = "".join(current).strip()
                if sentence:
                    sentences.append(sentence)
                current = []
    tail = "".join(current).strip()
    if tail:
        sentences.append(tail)
    return sentences


def sentence_count(s: str) -> int:
    """len(sentence_split(s))."""
    return len(sentence_split(s))


def contains(hay: str, ndl: str) -> bool:
    """casefold(ndl) is a substring of casefold(hay)."""
    return casefold(ndl) in casefold(hay)


def quote_match(text: str, q: str) -> bool:
    """normalize with case PRESERVED; q must be a substring of text after both
    are whitespace-normalized (V-DR-05)."""
    def _norm_case_preserved(x: str) -> str:
        x = unicodedata.normalize("NFC", x)
        x = _WHITESPACE_RE.sub(" ", x)
        return x.strip()

    return _norm_case_preserved(q) in _norm_case_preserved(text)


_YEAR_RANGE_RE = re.compile(r"^\s*(\d{4})\s*(?:-\s*(\d{4}))?\s*$")

# Unicode dash/tilde variants a human types in a period range that mean "-"
# (docs/09 §0, D10): en dash, em dash, figure/horizontal/non-breaking hyphens,
# minus sign, fullwidth hyphen, and the fullwidth "~" range marker. Normalized to
# a plain ASCII hyphen-minus before year-range parsing so "2020–2025" (en dash)
# reads as "2020-2025" (the live run rejected 7/8 nodes on this alone).
_DASH_VARIANTS = "‐‑‒–—―−－～〜~"
_DASH_RE = re.compile(f"[{re.escape(_DASH_VARIANTS)}]")


def normalize_dashes(s: str) -> str:
    """Map every Unicode dash/range-tilde variant to a plain ASCII '-' (docs/09
    §0, D10). Used before year-range parsing so an en/em-dashed period is
    compatible with a hyphenated one."""
    return _DASH_RE.sub("-", s or "")


def _parse_year_range(v: str) -> tuple[int, int] | None:
    """Parse 'YYYY' or 'YYYY-YYYY' into an inclusive (lo, hi) range."""
    m = _YEAR_RANGE_RE.match(normalize_dashes(v))
    if not m:
        return None
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo
    if hi < lo:
        lo, hi = hi, lo
    return (lo, hi)


def _period_compatible(a: str, b: str) -> bool:
    ra = _parse_year_range(a)
    rb = _parse_year_range(b)
    if ra is not None and rb is not None:
        # year-ranges intersect
        return ra[0] <= rb[1] and rb[0] <= ra[1]
    # unparseable => substring test either direction (case-insensitive)
    return contains(a, b) or contains(b, a)


def scope_compatible(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """For every key present in BOTH objects, compatibility must hold; missing
    keys never conflict (docs/09 §0).

    period    - compatible iff the year-ranges intersect (parse 'YYYY' and
                'YYYY-YYYY'; unparseable => substring test either direction).
    region    - equal after casefold.
    actors /
    mechanisms - non-empty intersection after casefold() of each element.
    """
    a = a or {}
    b = b or {}
    for key in ("period", "region", "actors", "mechanisms"):
        if key not in a or a.get(key) is None:
            continue
        if key not in b or b.get(key) is None:
            continue
        av = a[key]
        bv = b[key]
        if key == "period":
            if not _period_compatible(str(av), str(bv)):
                return False
        elif key == "region":
            if casefold(str(av)) != casefold(str(bv)):
                return False
        else:  # actors / mechanisms
            aset = {casefold(str(x)) for x in av}
            bset = {casefold(str(x)) for x in bv}
            if not (aset & bset):
                return False
    return True
