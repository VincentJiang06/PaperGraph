#!/usr/bin/env python3
"""RT-5 measurement: metadata heuristic vs render-diff oracle, over a real-paper corpus.

For every span the heuristic sends to non_rendered_text -> ask the oracle (precision).
For a fixed-seed random sample of spans the heuristic sends to rendered_text -> ask the
oracle (recall / missed invisible text). Deterministic: seed is fixed, no timestamps.
"""
import sys, random, pymupdf, classify, renderdiff2 as rd

SAMPLE = int(sys.argv[2]) if len(sys.argv) > 2 else 60
SEED = 20260817

def run(path):
    doc = pymupdf.open(path)
    off = classify.off_layer_names(doc)
    for c in doc.layer_ui_configs():
        doc.set_layer_ui_config(c["number"], action=0)
    flagged, accepted = [], []
    for pno, page in enumerate(doc):
        for row in classify.classify_page(page, off):
            if not row["text"].strip():
                continue   # whitespace-only spans carry no ink and no citable content
            rec = (pno, row["bbox"], row)   # bbox comes straight off the row; seqno is NOT a key
            (flagged if row["channel"] == "non_rendered_text" else accepted).append(rec)

    rnd = random.Random(SEED)
    samp = accepted if len(accepted) <= SAMPLE else rnd.sample(accepted, SAMPLE)

    tp = fp = 0
    fp_examples = []
    for pno, bbox, row in flagged:
        ch, mx, _ = rd.ink_delta(path, pno, bbox)
        if rd.verdict(ch, mx) == "INVISIBLE":
            tp += 1
        else:
            fp += 1
            if len(fp_examples) < 3:
                fp_examples.append((row["reasons"], row["text"][:36], ch, mx))

    miss = 0
    miss_examples = []
    for pno, bbox, row in samp:
        ch, mx, _ = rd.ink_delta(path, pno, bbox)
        if rd.verdict(ch, mx) == "INVISIBLE":
            miss += 1
            if len(miss_examples) < 3:
                miss_examples.append((row["text"][:36], row["size"], row["color"], ch, mx))

    print("%-26s spans=%-6s flagged=%-5s oracle_agrees(TP)=%-5s oracle_disagrees(FP)=%-4s "
          "| sampled_accepted=%-4s oracle_says_invisible(FN)=%s"
          % (path, len(flagged) + len(accepted), len(flagged), tp, fp, len(samp), miss))
    for r, t, ch, mx in fp_examples:
        print("     FP: %r reasons=%s changed_px=%s max_delta=%s" % (t, ";".join(r), ch, mx))
    for t, s, c, ch, mx in miss_examples:
        print("     FN: %r size=%s color=%s changed_px=%s max_delta=%s" % (t, s, c, ch, mx))

if __name__ == "__main__":
    for p in sys.argv[1].split(","):
        run(p)
