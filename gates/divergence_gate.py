"""Gate 1 — DIVERGENCE. Scores position-space coverage of the paper.

Ground truth is <run>/positions.md (the cartographer's map of the FIELD's positions).
The paper (<run>/paper.md) signals engagement with inline tags [P1]..[Pn] and [OBJ], and
may list deliberately-out-of-scope positions in an "## Excluded" section.

  coverage    = handled / total       handled = engaged OR excluded-with-reason
  engagement  = engaged / total       (excluded does NOT count as engaged)
  objection   = is [OBJ] present with a real argument around it?

A tag counts as a *real argument* only if the sentence/line carrying it has enough prose
around the tag (not a bare "[P3]" mention). PASS iff coverage==1.0 AND engagement>=K AND
objection engaged. K is read from the field-weight line in paper.md, default mixed=0.6.

Usage: python3 gates/divergence_gate.py runs/<slug>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

K_BY_WEIGHT = {"humanities": 0.8, "mixed": 0.6, "science": 0.5}
# A tagged position must sit in a PARAGRAPH (blank-line block) carrying at least this much
# non-tag prose to count as a real argument. Paragraph-based (not line-based) so a bare
# namedrop on a wrapped line can't clear the bar — engagement needs an actual argument.
MIN_ARG_CHARS = 200


def paragraph_span(md: str, pos: int) -> tuple[int, int]:
    """Span of the blank-line-delimited paragraph containing offset `pos`."""
    start = md.rfind("\n\n", 0, pos)
    start = 0 if start == -1 else start + 2
    end = md.find("\n\n", pos)
    end = len(md) if end == -1 else end
    return start, end


def _prose_len(md: str, pos: int) -> int:
    """Length of the tag-stripped prose in the paragraph around `pos`."""
    s, e = paragraph_span(md, pos)
    return len(re.sub(r"\[(?:P\d+|OBJ)\]", "", md[s:e]).strip())


def parse_positions(md: str) -> tuple[list[str], bool]:
    """Return (position ids like ['P1','P2',...], has_objection_block)."""
    ids = re.findall(r"(?m)^##\s+(P\d+)\s*:", md)
    has_obj = bool(re.search(r"(?m)^##\s+STRONGEST-OBJECTION\b", md))
    return ids, has_obj


def parse_excluded(md: str) -> set[str]:
    """Ids listed under an '## Excluded' section with a reason on the line."""
    m = re.search(r"(?m)^##\s+Excluded\b(.*?)(?=^##\s|\Z)", md, flags=re.S)
    if not m:
        return set()
    out = set()
    for line in m.group(1).splitlines():
        hit = re.search(r"\[(P\d+)\]", line)
        # require a reason: some prose beyond the bare tag
        if hit and len(re.sub(r"\[P\d+\]", "", line).strip(" -\t")) >= 8:
            out.add(hit.group(1))
    return out


def engaged_ids(md: str, exclude_section_span=None) -> set[str]:
    """Ids whose inline tag sits inside a paragraph carrying real argument prose."""
    out = set()
    for m in re.finditer(r"\[(P\d+)\]", md):
        if exclude_section_span and exclude_section_span[0] <= m.start() < exclude_section_span[1]:
            continue
        if _prose_len(md, m.start()) >= MIN_ARG_CHARS:
            out.add(m.group(1))
    return out


def objection_engaged(md: str) -> bool:
    return any(_prose_len(md, m.start()) >= MIN_ARG_CHARS
              for m in re.finditer(r"\[OBJ\]", md))


def field_weight(md: str) -> str:
    m = re.search(r"(?i)field[-_ ]?weight\s*[:=]\s*(humanities|mixed|science)", md)
    return m.group(1).lower() if m else "mixed"


def main(run_arg: str):
    run = Path(run_arg)
    pos_f, paper_f = run / "positions.md", run / "paper.md"
    if not pos_f.is_file():
        print(f"no positions.md in {run}"); sys.exit(2)
    if not paper_f.is_file():
        print(f"no paper.md in {run}"); sys.exit(2)
    pos_md, paper_md = pos_f.read_text(), paper_f.read_text()

    ids, has_obj = parse_positions(pos_md)
    if not ids:
        print("positions.md has no P-blocks"); sys.exit(2)
    total = len(ids)

    excl_m = re.search(r"(?m)^##\s+Excluded\b", paper_md)
    excl_span = (excl_m.start(), len(paper_md)) if excl_m else None
    excluded = parse_excluded(paper_md) & set(ids)
    engaged = engaged_ids(paper_md, excl_span) & set(ids)
    handled = engaged | excluded
    obj_ok = objection_engaged(paper_md) if has_obj else False

    coverage = len(handled) / total
    engagement = len(engaged) / total
    weight = field_weight(paper_md)
    K = K_BY_WEIGHT[weight]
    passed = coverage == 1.0 and engagement >= K and obj_ok

    lines = ["## DIVERGENCE gate", "",
             f"field-weight: **{weight}** (engagement threshold K={K:.0%})",
             f"coverage: **{len(handled)}/{total} = {coverage:.0%}** "
             f"(engaged or consciously excluded)",
             f"engagement: **{len(engaged)}/{total} = {engagement:.0%}** "
             f"{'OK' if engagement >= K else 'BELOW K'}",
             f"strongest-objection engaged: **{'yes ✅' if obj_ok else 'no ❌'}**"
             + ("" if has_obj else "  (no STRONGEST-OBJECTION block in positions.md)"),
             "",
             f"verdict: **{'PASS ✅' if passed else 'FAIL ❌'}**", ""]
    for pid in ids:
        state = "engaged" if pid in engaged else ("excluded" if pid in excluded else "UNHANDLED")
        mark = "✅" if pid in engaged else ("➖" if pid in excluded else "❌")
        lines.append(f"- {mark} `{pid}`: {state}")

    report = run / "gate_report.md"
    prev = report.read_text() if report.is_file() else ""
    prev = re.split(r"(?m)^## DIVERGENCE gate$.*?(?=^## |\Z)", prev, flags=re.S)
    head = "".join(prev).rstrip()
    report.write_text((head + "\n\n" if head else "") + "\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
