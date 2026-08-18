#!/usr/bin/env python3
"""M0-2 PDF arm, v2.

Fixes vs v1:
  * PROSE-ONLY sampling. v1 drew from any block >120 chars, which included figure label
    soup ("Lstm Lstm Lstm", "T1 ... TN T[SEP]"); those fail for reading-order reasons, not
    fidelity reasons, and dragged BERT down to 24%. A real quote comes from prose.
  * Reports the §1.2.2 rule AS WRITTEN and the proposed symmetric fix side by side.

Cross-tool by design: quotes are copied out of `pdftotext -layout` (the text layer a viewer
hands a human) and matched against PyMuPDF get_text() (our pipeline). Fixed seed.
"""
import sys, re, random, subprocess, pymupdf, norm
from rapidfuzz import fuzz

SEED = 20260817
N = 120

def viewer_text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"],
                          capture_output=True).stdout.decode("utf-8", "replace")

def is_prose(block):
    b = block.strip()
    if len(b) < 200:
        return False
    letters = len(re.findall(r"[A-Za-z一-鿿]", b))
    if letters / max(1, len(b)) < 0.72:      # formulas / tables / label soup are symbol-heavy
        return False
    toks = b.split()
    if toks and sum(len(t) for t in toks) / len(toks) < 3.0:   # label soup = many 1-2 char tokens
        return False
    if not re.search(r"[.。]\s", b):          # prose has sentence enders
        return False
    return True

def sample_quotes(text, n, rnd):
    paras = [p for p in re.split(r"\n\s*\n", text) if is_prose(p)]
    qs, tries = [], 0
    while len(qs) < n and tries < n * 80 and paras:
        tries += 1
        body = rnd.choice(paras).strip()
        zh = norm.has_cjk(body)
        L = rnd.randint(18, 45) if zh else rnd.randint(45, 130)
        if len(body) <= L + 2:
            continue
        i = rnd.randint(0, len(body) - L - 1)
        q = body[i:i + L]
        if len(q.strip()) < 10 or not re.search(r"[A-Za-z一-鿿]", q):
            continue
        qs.append(q)
    return qs

def run(path, label):
    rnd = random.Random(SEED)
    quotes = sample_quotes(viewer_text(path), N, rnd)
    if not quotes:
        print("%-20s NO PROSE BLOCKS FOUND" % label)
        return
    snap = "\n".join(p.get_text() for p in pymupdf.open(path))
    zh_n = sum(1 for q in quotes if norm.has_cjk(q))

    raw = sum(1 for q in quotes if q in snap)
    v1 = sum(1 for q in quotes if norm.quote_faithful(q, snap, True, norm.compare_key))
    v2 = sum(1 for q in quotes if norm.quote_faithful(q, snap, True, norm.compare_key_v2))
    v3 = sum(1 for q in quotes if norm.quote_faithful(q, snap, True, norm.compare_key_v3))
    miss2 = [q for q in quotes if not norm.quote_faithful(q, snap, True, norm.compare_key_v3)]
    k2 = norm.compare_key_v3(snap, True)
    near = sum(1 for q in miss2 if fuzz.partial_ratio(norm.compare_key_v3(q, True), k2) >= 95)

    t = len(quotes)
    print("%-20s n=%-4s zh=%-4s | raw=%5.1f%% | as_written=%5.1f%% | fix_between_cjk=%5.1f%% "
          "| fix_adjacent_cjk=%5.1f%% | misses=%-4s near>=95=%s"
          % (label, t, zh_n, 100.0*raw/t, 100.0*v1/t, 100.0*v2/t, 100.0*v3/t, len(miss2), near))
    return quotes, miss2, snap

if __name__ == "__main__":
    for spec in sys.argv[1:]:
        p, lab = spec.split("=")
        run(p, lab)
