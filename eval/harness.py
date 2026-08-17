"""EVAL harness — the executable, objective core of the independent judge.

Its ground truth is an ANSWER KEY derived from REAL published papers (eval/corpus/<topic>/
answer_key.json), built blind to the paper under test. The harness scores a paper against that
external key — so a cozy, self-authored positions.md that omits a position the real literature
insists on is EXPOSED here, which the in-loop gate (that trusts the author's own map) cannot do.

What is mechanical/objective and lives here:
  - independent-coverage: for each answer-key position (from the literature), does the paper
    engage it? (a distinctive key_term of that position appears in a real paragraph).
  - reproduce-rate: shell out to the rigor gate (numbers reproduce or they don't).
The subjective dimensions (steelman fidelity, objection robustness, referee panel — eval/
protocol.md) are supplied as agent verdicts in eval/verdicts/<paper>.json and folded in here.

Usage:
  python3 eval/harness.py score  <run_dir> --key eval/corpus/<topic>/answer_key.json [--arm gated]
  python3 eval/harness.py cover  <paper.md|paper.txt> --key <answer_key.json>   # external paper, coverage only
  python3 eval/harness.py fetch  <url> [-o out.txt]                             # grab a real paper's text
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_VERSION = "0.3.0"
MIN_ARG_CHARS = 200  # a position is "engaged" only inside a real paragraph, not a passing mention


def fetch_text(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PaperGraph eval)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read(4_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
    except Exception as e:
        print(f"fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    return html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))


def paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def coverage(paper_text: str, positions: list[dict]) -> dict:
    """Each position is engaged if one of its key_terms sits in a >=MIN_ARG_CHARS paragraph."""
    paras = [p for p in paragraphs(paper_text) if len(re.sub(r"\s+", " ", p).strip()) >= MIN_ARG_CHARS]
    low_paras = [p.lower() for p in paras]
    covered, missed = [], []
    for pos in positions:
        terms = [t.lower() for t in pos.get("key_terms", []) if t.strip()]
        hit = next((t for t in terms if any(t in lp for lp in low_paras)), None)
        (covered if hit else missed).append({"id": pos["id"], "name": pos.get("name", ""),
                                             "via": hit, "terms": terms})
    total = len(positions)
    return {"total": total, "covered": covered, "missed": missed,
            "rate": (total - len(missed)) / total if total else 0.0}


def reproduce_rate(run_dir: Path) -> tuple[float | None, str]:
    """Objective rigor input: run the rigor gate as an external tool, parse its reproduce-rate."""
    if not (run_dir / "claims.tsv").is_file():
        return None, "no claims.tsv (external paper — rigor N/A)"
    try:
        out = subprocess.run([sys.executable, str(ROOT / "gates" / "rigor_gate.py"), str(run_dir)],
                             cwd=ROOT, capture_output=True, text=True, timeout=600)
    except Exception as e:
        return None, f"rigor gate crashed: {e}"
    m = re.search(r"reproduce-rate:\s*\*\*(\d+)/(\d+)", out.stdout)
    if not m:
        return None, "could not parse rigor gate output"
    n, d = int(m.group(1)), int(m.group(2))
    return (n / d if d else 0.0), f"{n}/{d}"


def load_verdicts(paper: str) -> dict:
    """Agent-supplied subjective dimensions (eval/protocol.md), if the panel has been run."""
    f = ROOT / "eval" / "verdicts" / f"{paper}.json"
    return json.loads(f.read_text()) if f.is_file() else {}


def reconcile(cov: dict, v: dict) -> tuple[list[str], list[str]]:
    """D1 is a fast term-based SCREEN with false negatives (vocabulary mismatch); D2 (agent,
    substance) is authoritative. A screen-missed position is RESCUED if D2 scored it >=1.
    Returns (unrescued_missed_ids, rescued_ids). Without D2, all screen-misses stand (provisional)."""
    steel = v.get("steelman_by_pos") or {}
    missed = [m["id"] for m in cov["missed"]]
    if not steel:
        return missed, []
    unrescued = [mid for mid in missed if steel.get(mid, 0) < 1]
    rescued = [mid for mid in missed if steel.get(mid, 0) >= 1]
    return unrescued, rescued


def verdict(cov: dict, repro: float | None, v: dict) -> tuple[str, list[str]]:
    """Apply EVAL.md kill-criteria over whatever dimensions are available."""
    fails = []
    unrescued, _ = reconcile(cov, v)
    if unrescued:
        tag = "" if not v.get("steelman_by_pos") else " (D2-confirmed)"
        fails.append(f"coverage: {len(unrescued)} position(s) not engaged{tag}: "
                     f"{', '.join(unrescued)}")
    if repro is not None and repro < 1.0:
        fails.append(f"reproduce-rate {repro:.0%} < 100%")
    if v.get("steelman_min") is not None and v["steelman_min"] < 1:
        fails.append("a position was steelman-scored 0 (strawman)")
    if v.get("objection_robust") is False:
        fails.append("a materially-stronger unaddressed objection exists")
    if v.get("claim_coverage") is not None and v["claim_coverage"] < 1.0:
        fails.append(f"claim-coverage {v['claim_coverage']:.0%} < 100%")
    if v.get("referee_verdict") == "reject":
        fails.append("referee modal verdict = reject")
    return ("SHIP" if not fails else "REVISE"), fails


def score(run_arg: str, key_path: str, arm: str = "gated"):
    run = Path(run_arg).resolve()
    paper_f = run / "paper.md"
    if not paper_f.is_file():
        print(f"no paper.md in {run}"); sys.exit(2)
    key = json.loads(Path(key_path).read_text())
    paper = run.name
    cov = coverage(paper_f.read_text(), key["positions"])
    repro, repro_note = reproduce_rate(run)
    v = load_verdicts(paper)
    result, fails = verdict(cov, repro, v)

    lines = [f"# EVAL report — {paper} (arm: {arm})", "",
             f"eval-version: {EVAL_VERSION} · answer-key: `{key_path}` (from real literature)", "",
             f"## Verdict: **{result}**"]
    if fails:
        lines += ["", "Kill-criteria tripped:"] + [f"- ❌ {f}" for f in fails]
    unrescued, rescued = reconcile(cov, v)
    screen = f"{cov['total']-len(cov['missed'])}/{cov['total']} = {cov['rate']:.0%}"
    recon = f"{cov['total']-len(unrescued)}/{cov['total']} = {(cov['total']-len(unrescued))/cov['total']:.0%}"
    lines += ["", "## D1 — independent coverage (vs the literature's positions)",
              f"screen: **{screen}**" + (f" · reconciled with D2: **{recon}**" if v.get("steelman_by_pos") else " (screen only — run D2 to confirm)")]
    for c in cov["covered"]:
        lines.append(f"- ✅ `{c['id']}` {c['name']} — via \"{c['via']}\"")
    for c in cov["missed"]:
        if c["id"] in rescued:
            lines.append(f"- ↺ `{c['id']}` {c['name']} — screen-missed but D2 judged it engaged (rescued)")
        else:
            lines.append(f"- ❌ `{c['id']}` {c['name']} — NOT engaged (terms: {', '.join(c['terms'][:4])})")
    lines += ["", "## D4 — reproduce-rate (objective rigor input)", f"{repro_note}"]
    if v:
        lines += ["", "## D2 — steelman fidelity (per position, 0/1/2)",
                  "  " + ", ".join(f"{k}:{s}" for k, s in v.get("steelman_by_pos", {}).items())
                  + f"  → min **{v.get('steelman_min', '?')}**",
                  "", "## D3 — objection robustness",
                  f"robust: **{v.get('objection_robust', '?')}**"]
        if v.get("stronger_objection"):
            lines.append(f"- stronger unaddressed objection: {v['stronger_objection']}")
        lines += ["", "## D4b — claim completeness & honesty",
                  f"claim-coverage: **{v.get('ledgered', '?')}/{v.get('total_empirical', '?')} "
                  f"= {v.get('claim_coverage', '?')}**"]
        for u in v.get("uncited_load_bearing", []):
            lines.append(f"- uncited: {u}")
        for h in v.get("honesty_flags", []):
            lines.append(f"- ⚠ honesty: {h}")
        lines += ["", "## D5 — referee panel",
                  f"modal verdict: **{v.get('referee_verdict', '?')}**"]
        for r in v.get("referee_panel", []):
            lines.append(f"- {r.get('lens', '?')}: {r.get('verdict', '?')} {r.get('scores', '')}")
    else:
        lines += ["", "_Subjective dimensions (D2/D3/D5) not yet run — dispatch eval/protocol.md._"]

    (ROOT / "eval" / "reports").mkdir(exist_ok=True)
    (ROOT / "eval" / "reports" / f"{paper}.md").write_text("\n".join(lines) + "\n")

    sb = ROOT / "eval" / "scoreboard.tsv"
    note = ("missed:" + ",".join(unrescued)) if unrescued else "-"
    if rescued:
        note += f" (D2-rescued:{','.join(rescued)})"
    row = [paper, arm, EVAL_VERSION, f"{cov['rate']:.2f}", (f"{repro:.2f}" if repro is not None else "NA"),
           str(v.get("steelman_min", "?")), str(v.get("objection_robust", "?")),
           str(v.get("claim_coverage", "?")), str(v.get("referee_verdict", "?")), result, note]
    with sb.open("a") as f:
        f.write("\t".join(row) + "\n")
    print("\n".join(lines))
    sys.exit(0 if result == "SHIP" else 1)


def cover_only(paper_file: str, key_path: str):
    key = json.loads(Path(key_path).read_text())
    text = Path(paper_file).read_text()
    cov = coverage(text, key["positions"])
    print(f"independent-coverage: {cov['total']-len(cov['missed'])}/{cov['total']} = {cov['rate']:.0%}")
    for c in cov["covered"]:
        print(f"  ✅ {c['id']} {c['name']} — via \"{c['via']}\"")
    for c in cov["missed"]:
        print(f"  ❌ {c['id']} {c['name']} — NOT engaged")


def main(argv: list[str]):
    if not argv:
        print(__doc__); sys.exit(2)
    cmd = argv[0]
    if cmd == "fetch":
        url = argv[1]
        out = argv[argv.index("-o") + 1] if "-o" in argv else None
        text = fetch_text(url)
        if text is None:
            sys.exit(1)
        (Path(out).write_text(text) if out else print(text[:4000]))
    elif cmd == "cover":
        cover_only(argv[1], argv[argv.index("--key") + 1])
    elif cmd == "score":
        arm = argv[argv.index("--arm") + 1] if "--arm" in argv else "gated"
        score(argv[1], argv[argv.index("--key") + 1], arm)
    else:
        print(f"unknown command {cmd!r}"); sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
