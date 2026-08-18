#!/usr/bin/env python3
"""M0-2 web arm, v2: separate COVERAGE from FIDELITY.

v1 mixed two different failures into one number. trafilatura strips boilerplate, so most
DOM prose blocks simply are not in the pipeline text at all -- that is a coverage loss, and
it makes quote_faithful fail for a reason the producer never controlled. Reported apart:

  coverage  = share of DOM prose blocks that survive into the pipeline extraction
              (block-level fuzzy presence, partial_ratio >= 90)
  fidelity  = exact-substring hit rate for quotes drawn ONLY from covered blocks
"""
import sys, random, norm, quote_web, quote_pdf2
from rapidfuzz import fuzz

SEED = 20260817
N = 120

def run(path, label):
    html = open(path, "rb").read().decode("utf-8", "replace")
    dom = quote_web.dom_text(html)
    snap = quote_web.pipeline_text(html)
    snap_k = norm.compare_key_v3(snap)

    blocks = [b.strip() for b in dom.split("\n") if quote_pdf2.is_prose(b)]
    if not blocks:
        import re
        blocks = [b.strip() for b in re.split(r"(?<=[.。])\s{2,}", dom) if quote_pdf2.is_prose(b)]
    covered = [b for b in blocks if fuzz.partial_ratio(norm.compare_key_v3(b), snap_k) >= 90]
    cov = 100.0 * len(covered) / max(1, len(blocks))

    if not covered:
        print("%-16s blocks=%-5s coverage=%5.1f%%  -- no covered prose block to sample from"
              % (label, len(blocks), cov))
        return
    rnd = random.Random(SEED)
    quotes = quote_pdf2.sample_quotes("\n\n".join(covered), N, rnd)
    t = max(1, len(quotes))
    zh_n = sum(1 for q in quotes if norm.has_cjk(q))
    raw = sum(1 for q in quotes if q in snap)
    v1 = sum(1 for q in quotes if norm.quote_faithful(q, snap, False, norm.compare_key))
    v3 = sum(1 for q in quotes if norm.quote_faithful(q, snap, False, norm.compare_key_v3))
    miss = [q for q in quotes if not norm.quote_faithful(q, snap, False, norm.compare_key_v3)]
    near = sum(1 for q in miss if fuzz.partial_ratio(norm.compare_key_v3(q), snap_k) >= 95)
    print("%-16s blocks=%-5s coverage=%5.1f%% | n=%-4s zh=%-4s | raw=%5.1f%% | as_written=%5.1f%% "
          "| fix_adjacent_cjk=%5.1f%% | misses=%-3s near>=95=%s"
          % (label, len(blocks), cov, len(quotes), zh_n, 100.0*raw/t, 100.0*v1/t, 100.0*v3/t,
             len(miss), near))

if __name__ == "__main__":
    for spec in sys.argv[1:]:
        p, lab = spec.split("=")
        run(p, lab)
