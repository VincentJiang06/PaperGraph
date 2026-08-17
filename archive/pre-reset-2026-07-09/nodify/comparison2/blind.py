"""Blind the 3 mode-articles per topic for the judge panel.

Removes every MODE tell (not every quality signal):
  - inline cites  (S3) / (cite: DOC-0002)      -> [n]  in appearance order
  - reference list  - (S1) .. / - S1: .. / - [DOC-0001] ..  -> uniform  [n] text
  - uniform header  ## 参考文献
Evidence provenance (NBER vs news, source breadth) is deliberately preserved —
that is real quality signal, not a mode tell; judges never learn the modes exist.

Slot assignment is a fixed Latin-square per topic (recorded in KEY.json, withheld
from judges) so no mode sits in the same slot every time.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

MODES = ("raw", "skills", "tree")
TOPICS = ("T1", "T2", "T3", "T4", "T5")

# deterministic slot map: topic -> {slot: mode}
SLOTS = {
    "T1": {"A": "raw",    "B": "skills", "C": "tree"},
    "T2": {"A": "tree",   "B": "raw",    "C": "skills"},
    "T3": {"A": "skills",  "B": "tree",   "C": "raw"},
    "T4": {"A": "raw",    "B": "tree",   "C": "skills"},
    "T5": {"A": "tree",   "B": "skills", "C": "raw"},
}

REFS_HDR = re.compile(r"\n#+\s*(?:参考文献|References|引用)[^\n]*\n")
# a parenthetical cite group: (S3) / (cite: DOC-0002) / （S2、S3、S8） / (S1, S2)
# ASCII or full-width parens accepted
CITE_GROUP = re.compile(
    r"[(（](?:cite:\s*)?((?:S\d+|DOC-\d{4})(?:\s*[、,，/和&\s]+(?:S\d+|DOC-\d{4}))*)[)）]")
CITE_ID = re.compile(r"S\d+|DOC-\d{4}")
REF_ID = re.compile(r"(S\d+|DOC-\d{4})")
STRAY = re.compile(r"\b(nd check|nd article|synthesis record|logic tree|DOC-\d{4})\b", re.I)


def blind_one(text: str) -> str:
    # split off references
    m = REFS_HDR.search(text)
    body, refs = (text[:m.start()], text[m.end():]) if m else (text, "")

    # 1) inline cites -> [n] in first-appearance order. ORDER_SCAN is CITE_GROUP
    #    without the required closing bracket, so it also captures the ids of a
    #    malformed leading cite like "(S8 <commentary>)" — every id gets a number.
    ORDER_SCAN = re.compile(
        r"[(（](?:cite:\s*)?((?:S\d+|DOC-\d{4})(?:\s*[、,，/和&\s]+(?:S\d+|DOC-\d{4}))*)")
    order: list[str] = []
    for mo in ORDER_SCAN.finditer(body):
        for sid in CITE_ID.findall(mo.group(1)):
            if sid not in order:
                order.append(sid)
    # DOC ids are unambiguous — also register any that appear embedded mid-paren
    # (e.g. "（…,cite: DOC-0011）") which the paren-anchored scan above misses
    for sid in re.findall(r"DOC-\d{4}", body):
        if sid not in order:
            order.append(sid)
    newnum = {sid: i + 1 for i, sid in enumerate(order)}
    body = CITE_GROUP.sub(
        lambda mo: "".join(f"[{newnum[s]}]" for s in CITE_ID.findall(mo.group(1))),
        body)
    # embedded / bare DOC cites (drops any orphan "cite:" prefix)
    body = re.sub(r"(?:cite:\s*)?(DOC-\d{4})",
                  lambda mo: f"[{newnum[mo.group(1)]}]", body)
    # mop up any malformed leading "(Sn <text>)" the group regex didn't close
    body = re.sub(r"[(（](S\d+)(?=\D)",
                  lambda mo: f"（[{newnum[mo.group(1)]}]，" if mo.group(1) in newnum
                  else mo.group(0), body)

    # 2) rebuild references uniformly, in new-number order
    ref_text: dict[str, str] = {}
    for line in refs.splitlines():
        if not line.strip():
            continue
        idm = REF_ID.search(line)
        if not idm:
            continue
        sid = idm.group(1)
        # strip bullet, the id token, colons/brackets/parens around it
        t = line
        t = re.sub(r"^[\s\-*•]+", "", t)
        t = re.sub(r"\(?\[?" + re.escape(sid) + r"\]?\)?[:.]?\s*", "", t, count=1)
        ref_text[sid] = t.strip()

    out_refs = ["## 参考文献", ""]
    for sid in order:
        out_refs.append(f"[{newnum[sid]}] {ref_text.get(sid, '(来源)')}")

    result = body.rstrip() + "\n\n" + "\n".join(out_refs) + "\n"
    # 3) scrub any residual mode tells in the body prose
    result = STRAY.sub("(证据记录)", result)
    return result


def main(base: str = ".") -> None:
    base = Path(base)
    outdir = base / "blinded"
    key = {}
    for t in TOPICS:
        (outdir / t).mkdir(parents=True, exist_ok=True)
        key[t] = {}
        for slot, mode in SLOTS[t].items():
            art = base / "runs" / t / mode / "article.md"
            if not art.is_file():
                key[t][slot] = f"{mode} (MISSING)"
                continue
            blinded = blind_one(art.read_text(encoding="utf-8"))
            (outdir / t / f"Article-{slot}.md").write_text(blinded, encoding="utf-8")
            key[t][slot] = mode
    (outdir / "KEY.json").write_text(json.dumps(key, ensure_ascii=False, indent=2))
    print("blinded ->", outdir)
    print(json.dumps(key, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
