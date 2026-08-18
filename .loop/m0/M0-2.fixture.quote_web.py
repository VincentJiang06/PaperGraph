#!/usr/bin/env python3
"""M0-2 web arm: cross-extractor quote fidelity on real pages.

The product situation: our snapshot stores rendered_text from ONE extractor; the author
copies the quote out of a different rendering (their browser, or a different library).
So the test is cross-extractor:
  "human copy"       = BeautifulSoup(...).get_text(" ")   -- flat DOM text, closest offline
                        proxy for what a browser hands the clipboard
  "snapshot extract" = trafilatura.extract(...)           -- our pipeline's main-content path
Fixed seed, snapshots are local files with recorded sha256, so the run is deterministic.
"""
import sys, re, random, pymupdf, norm, trafilatura
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
import quote_pdf2

SEED = 20260817
N = 120

import innertext
def dom_text(html):
    """Browser-faithful innerText (see innertext.py). The earlier get_text(' ') proxy
    injected a space at every inline boundary, turning <sup>[66]</sup> into ' [ 66 ] '."""
    return innertext.inner_text(html)

def pipeline_text(html):
    return trafilatura.extract(html, include_comments=False, include_tables=True) or ""

def run(path, label):
    html = open(path, "rb").read().decode("utf-8", "replace")
    copied_src = dom_text(html)
    snap = pipeline_text(html)
    if len(snap) < 500:
        print("%-16s PIPELINE EXTRACTION TOO SHORT (%s chars)" % (label, len(snap)))
        return
    rnd = random.Random(SEED)
    quotes = quote_pdf2.sample_quotes(copied_src, N, rnd)
    if not quotes:
        print("%-16s NO PROSE BLOCKS" % label)
        return
    t = len(quotes)
    zh_n = sum(1 for q in quotes if norm.has_cjk(q))
    raw = sum(1 for q in quotes if q in snap)
    v1 = sum(1 for q in quotes if norm.quote_faithful(q, snap, False, norm.compare_key))
    v3 = sum(1 for q in quotes if norm.quote_faithful(q, snap, False, norm.compare_key_v3))
    miss = [q for q in quotes if not norm.quote_faithful(q, snap, False, norm.compare_key_v3)]
    k = norm.compare_key_v3(snap)
    near = sum(1 for q in miss if fuzz.partial_ratio(norm.compare_key_v3(q), k) >= 95)
    print("%-16s n=%-4s zh=%-4s | raw=%5.1f%% | as_written=%5.1f%% | fix_adjacent_cjk=%5.1f%% "
          "| misses=%-4s near>=95=%s"
          % (label, t, zh_n, 100.0*raw/t, 100.0*v1/t, 100.0*v3/t, len(miss), near))
    return quotes, miss, snap

if __name__ == "__main__":
    for spec in sys.argv[1:]:
        p, lab = spec.split("=")
        run(p, lab)
