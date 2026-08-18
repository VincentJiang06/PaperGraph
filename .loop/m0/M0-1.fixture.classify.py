#!/usr/bin/env python3
"""RT-5 reference classifier: split a PDF page's text into rendered_text / non_rendered_text.

Uses ONLY PyMuPDF page.get_texttrace(), which exposes per-span:
  type (3 = Tr 3 invisible), color (RGB float), opacity, size, bbox, layer (OCG name), seqno (z-order).
Occlusion is decided by comparing seqno against opaque fills from page.get_drawings().
"""
import sys, json, pymupdf

TINY = 4.0          # pt; below this a human cannot read it at 100%
CONTRAST = 0.10     # euclidean RGB distance to the painted background

def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def off_layer_names(doc):
    """Names of OCGs whose DEFAULT state is OFF (i.e. /OCProperties /D /OFF).
    NOTE: doc.get_ocgs()['on'] does NOT reflect /D /OFF -- it reported on=True for a
    layer that layer_ui_configs() correctly reports as off. Use layer_ui_configs()."""
    return {c["text"] for c in doc.layer_ui_configs() if not c.get("on")}


def classify_page(page, off_layers=frozenset()):
    drawings = [d for d in page.get_drawings()
                if d.get("fill") is not None and d.get("fill_opacity", 1) in (None, 1, 1.0)]
    prect = page.rect
    out = []
    for sp in page.get_texttrace():
        txt = "".join(chr(c[0]) for c in sp["chars"])
        bbox = pymupdf.Rect(sp["bbox"])
        reasons = []

        if sp["type"] == 3:
            reasons.append("render-mode-3-invisible")
        if sp.get("opacity", 1.0) is not None and sp.get("opacity", 1.0) < 0.05:
            reasons.append("alpha-zero")
        if sp["size"] < TINY:
            reasons.append("font-size-%.3gpt-below-%gpt" % (sp["size"], TINY))
        # ONLY a default-OFF layer hides text. Benign figure layers (Illustrator emits
        # these constantly) are ON by default and must NOT be flagged.
        if sp.get("layer") and sp["layer"] in off_layers:
            reasons.append("optional-content-group-OFF:%s" % sp["layer"])
        if not pymupdf.Rect(prect).intersects(bbox):
            reasons.append("outside-media-box")

        # background under this span = topmost opaque fill painted BEFORE it that contains it
        bg = (1.0, 1.0, 1.0)
        bg_src = "page-default-white"
        for d in drawings:
            if d.get("seqno", -1) < sp["seqno"] and pymupdf.Rect(d["rect"]).contains(bbox):
                bg, bg_src = d["fill"], "fill-seqno-%s" % d["seqno"]
        col = sp["color"] or (0.0, 0.0, 0.0)
        dist = sum((a - b) ** 2 for a, b in zip(col, bg)) ** 0.5
        if dist < CONTRAST:
            reasons.append("no-contrast-vs-%s(dist=%.3f)" % (bg_src, dist))

        # occlusion: an opaque fill painted AFTER this span that covers it
        for d in drawings:
            if d.get("seqno", -1) > sp["seqno"] and pymupdf.Rect(d["rect"]).contains(bbox):
                if abs(lum(d["fill"]) - lum(col)) < 0.6:
                    reasons.append("occluded-by-fill-seqno-%s" % d["seqno"])
                else:
                    reasons.append("occluded-by-fill-seqno-%s(high-contrast-overpaint)" % d["seqno"])

        # NOTE: seqno is the content-stream OPERATION index and is NOT unique per span --
        # one TJ array yields several spans sharing a seqno. Carry the bbox on the row;
        # never key a span lookup by seqno.
        out.append({"text": txt, "channel": "non_rendered_text" if reasons else "rendered_text",
                    "reasons": reasons, "size": round(sp["size"], 4), "bbox": tuple(sp["bbox"]),
                    "color": [round(v, 3) for v in col], "type": sp["type"], "seqno": sp["seqno"]})
    return out

def main(path, show_all=True):
    doc = pymupdf.open(path)
    off = off_layer_names(doc)              # record the OFF set BEFORE forcing layers on
    for cfg in doc.layer_ui_configs():      # force OCGs ON so hidden layers are *seen and classified*,
        doc.set_layer_ui_config(cfg["number"], action=0)   # not silently dropped
    rows = []
    for page in doc:
        rows += classify_page(page, off)
    r = sum(1 for x in rows if x["channel"] == "rendered_text")
    n = len(rows) - r
    print("SPANS=%d  rendered_text=%d  non_rendered_text=%d" % (len(rows), r, n))
    for x in rows:
        if show_all or x["channel"] == "non_rendered_text":
            print("[%-17s] %-46r  %s" % (x["channel"], x["text"][:46], ";".join(x["reasons"])))

if __name__ == "__main__":
    main(sys.argv[1], show_all=(len(sys.argv) < 3 or sys.argv[2] != "hidden-only"))
