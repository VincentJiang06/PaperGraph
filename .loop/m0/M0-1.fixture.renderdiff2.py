#!/usr/bin/env python3
"""Render-diff visibility oracle, v2.

Fixes vs v1:
  (a) render with the document's ORIGINAL layer config (v1 forced OCGs on, which made
      default-OFF layer text look visible);
  (b) report ink MAGNITUDE (changed-pixel count + max channel delta) instead of exact
      raster equality -- a 0.1pt glyph still flips one antialiased pixel, so byte equality
      classifies it as visible.
Enumeration of spans still forces layers on, so OFF-layer text is *seen and classified*
rather than silently dropped.
"""
import sys, pymupdf

DPI = 200
# Calibrated on the fixture + corpus: a 0.1pt run of 57 chars flips 8 px at max_delta=10;
# a legitimate 7.56pt period flips 10 px at max_delta=250. So CHANGED-PIXEL COUNT does not
# separate them -- contrast magnitude does. Use max_delta alone.
MIN_DELTA = 40          # 0..255; fainter than this against the background = no legible mark

def enumerate_spans(path):
    doc = pymupdf.open(path)
    for c in doc.layer_ui_configs():
        doc.set_layer_ui_config(c["number"], action=0)
    for pno, page in enumerate(doc):
        for sp in page.get_texttrace():
            yield pno, sp["bbox"], "".join(chr(c[0]) for c in sp["chars"]), sp["size"], sp["type"]

def _open_asis(path):
    return pymupdf.open(path)          # ORIGINAL layer config: OFF layers stay off

def ink_delta(path, pno, bbox):
    pad = pymupdf.Rect(bbox) + (-2, -2, 2, 2)
    d1 = _open_asis(path); p1 = d1[pno]
    clip = pymupdf.Rect(pad) & p1.rect
    if clip.is_empty:
        return 0, 0, "bbox-outside-page"
    a = p1.get_pixmap(dpi=DPI, clip=clip, annots=False)

    d2 = _open_asis(path); p2 = d2[pno]
    p2.add_redact_annot(pymupdf.Rect(bbox))
    p2.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                        graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                        text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    b = p2.get_pixmap(dpi=DPI, clip=clip, annots=False)
    if a.samples_mv.nbytes != b.samples_mv.nbytes:
        return -1, -1, "size-mismatch"
    sa, sb = a.samples, b.samples
    if sa == sb:
        return 0, 0, "ok"
    n = a.n
    changed = 0
    mx = 0
    for i in range(0, len(sa), n):
        dmax = max(abs(sa[i + k] - sb[i + k]) for k in range(min(3, n)))
        if dmax:
            changed += 1
            if dmax > mx:
                mx = dmax
    return changed, mx, "ok"

def verdict(changed, mx):
    if changed <= 0 or mx < MIN_DELTA:
        return "INVISIBLE"
    return "VISIBLE"

if __name__ == "__main__":
    path = sys.argv[1]
    needle = sys.argv[2] if len(sys.argv) > 2 else None
    for pno, bbox, txt, size, typ in enumerate_spans(path):
        if needle and needle not in txt:
            continue
        ch, mx, note = ink_delta(path, pno, bbox)
        print("%-9s changed_px=%-7s max_delta=%-5s %-18s p%-3s size=%-7s Tr=%s %r"
              % (verdict(ch, mx), ch, mx, note, pno, round(size, 3), typ, txt[:48]))
