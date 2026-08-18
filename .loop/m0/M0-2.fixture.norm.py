#!/usr/bin/env python3
"""01-CONTRACTS §1.2.2 normalisation, implemented as specified.

  NFKC -> unify quotes/dashes/ellipsis -> fold whitespace
  PDF專項: cross-line hyphen restoration + running header/footer removal
  中文專項: full/half-width unification, then strip ALL whitespace before comparing
Decision has exactly two exits: normalised quote is an exact substring of the normalised
snapshot text -> pass; otherwise fail (+F-28).
"""
import re, unicodedata, collections

QUOTES = {"‘": "'", "’": "'", "‚": "'", "‛": "'",
          "“": '"', "”": '"', "„": '"', "‟": '"',
          "′": "'", "″": '"', "«": '"', "»": '"',
          "「": '"', "」": '"', "『": '"', "』": '"'}
DASHES = {c: "-" for c in "‐‑‒–—―−－ー"}
ELLIPSIS = {"…": "...", "⋯": "...", "‥": "..."}
TABLE = {ord(k): v for k, v in list(QUOTES.items()) + list(DASHES.items()) + list(ELLIPSIS.items())}

CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿぀-ヿ가-힯]")

def has_cjk(s):
    return bool(CJK.search(s))

def restore_hyphens(s):
    """PDF 專項: 'exam-\\nple' -> 'example'. Only across a line break, only between letters."""
    return re.sub(r"(?<=[A-Za-z])[-‐‑]\s*\n\s*(?=[a-z])", "", s)

def strip_running_headers(pages, min_frac=0.6):
    """PDF 專項: drop lines that recur on >= min_frac of pages (running head / footer / DOI bar)."""
    if len(pages) < 3:
        return pages
    counts = collections.Counter()
    for p in pages:
        for ln in set(l.strip() for l in p.splitlines() if l.strip()):
            counts[ln] += 1
    need = max(2, int(len(pages) * min_frac))
    # a pure page number differs per page, so also drop short mostly-numeric lines
    drop = {ln for ln, c in counts.items() if c >= need and len(ln) > 3}
    out = []
    for p in pages:
        keep = [l for l in p.splitlines()
                if l.strip() not in drop and not re.fullmatch(r"[\s\d—\-·]{0,8}", l.strip() or "x")]
        out.append("\n".join(keep))
    return out

def normalize(s, pdf=False):
    if pdf:
        s = restore_hyphens(s)
    s = unicodedata.normalize("NFKC", s)      # also folds full-width ASCII to half-width
    s = s.translate(TABLE)
    s = s.replace("­", "")               # soft hyphen
    s = re.sub(r"[​-‏‪-‮﻿]", "", s)   # zero-width / bidi marks
    s = re.sub(r"\s+", " ", s).strip()        # fold whitespace
    return s

def compare_key(s, pdf=False):
    """AS WRITTEN in 01-CONTRACTS §1.2.2: if the string contains CJK, strip ALL whitespace.
    Applied per-string, so it is ASYMMETRIC: an English quote lifted out of a Chinese
    document keeps its spaces while the document side loses them -> can never match."""
    n = normalize(s, pdf=pdf)
    if has_cjk(n):
        n = re.sub(r"\s+", "", n)             # 中文專項: 整串去空白後比對
    return n

CJK_CLS = "㐀-䶿一-鿿豈-﫿぀-ヿ가-힯" \
          "，。！？；：、（）《》【】"

def compare_key_v2(s, pdf=False):
    """PROPOSED FIX: drop only whitespace sitting BETWEEN two CJK characters. Symmetric by
    construction (never branches on the string's language) and keeps Latin word boundaries,
    so 'the rapist' cannot collapse into 'therapist'."""
    n = normalize(s, pdf=pdf)
    prev = None
    while prev != n:
        prev = n
        n = re.sub(r"(?<=[%s])\s+(?=[%s])" % (CJK_CLS, CJK_CLS), "", n)
    return n

def compare_key_v3(s, pdf=False):
    """PROPOSED FIX (final): drop whitespace whenever EITHER neighbour is a CJK character.
    Chinese PDF extraction inserts spaces not only between two hanzi but also at every
    CJK/Latin and CJK/digit boundary ('FCM 算法', '算法 a'), which is why the between-CJK-only
    rule under-performs. Symmetric by construction: it never branches on the string's
    language, so an English quote taken from a Chinese document is normalised the same way
    on both sides. Latin-Latin spaces survive, so 'the rapist' cannot become 'therapist'."""
    n = normalize(s, pdf=pdf)
    prev = None
    while prev != n:
        prev = n
        n = re.sub(r"(?<=[%s])\s+" % CJK_CLS, "", n)
        n = re.sub(r"\s+(?=[%s])" % CJK_CLS, "", n)
    return n

def quote_faithful(quote, snapshot_text, pdf=False, key=None):
    k = key or compare_key
    return k(quote, pdf) in k(snapshot_text, pdf)
