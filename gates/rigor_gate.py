"""Gate 2 — RIGOR + TRACEABILITY. Thin wrapper over DVC (adopted, not rebuilt).

Reproducibility + provenance are delegated to DVC:
  - runs/<slug>/dvc.yaml has ONE stage per kind=data claim; the stage re-executes the
    transform (which writes metrics/<claim_id>.json = {"value": ...}).
  - `dvc repro -f` re-runs every transform from raw data; dvc.lock records the md5 of each
    raw dep + transform + produced metric — the provenance trail (可回溯).
This script keeps only what DVC does NOT do:
  - the claim<->number equality decision (numeric within 1% else exact string),
  - the verbatim source-quote check (kind=source),
  - the reproduce-rate, gate_report.md, and the PASS-iff-100% exit rule.

Usage: python3 gates/rigor_gate.py runs/<slug> [--verify-sources]

--verify-sources (optional, networked, NON-fatal): re-fetches each kind=source raw_ref URL and
checks the quote is present there — closing the "trust the saved sources/*.txt" gap for audits.
It never changes the pass/fail verdict (pages 403/paywall/JS-render), so the ship gate stays a
deterministic offline check; it only annotates gate_report.md with a ✅/⚠️ per source URL.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root; DVC + transforms run from here
WS = re.compile(r"\s+")
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def norm(s: str) -> str:
    return WS.sub(" ", s).strip().lower()


def as_num(s: str):
    m = NUM.search(str(s).replace(",", ""))
    return float(m.group()) if m else None


def dvc_repro(run: Path):
    """Re-execute every data transform via DVC. Returns (ok|None, log). None = no pipeline."""
    dvcyaml = run / "dvc.yaml"
    if not dvcyaml.is_file():
        return None, "no dvc.yaml (no kind=data claims to reproduce)"
    try:
        out = subprocess.run(
            [sys.executable, "-m", "dvc", "repro", "-f", str(dvcyaml.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, timeout=600)
    except Exception as e:
        return False, f"dvc repro crashed: {e}"
    log = (out.stdout + out.stderr).strip()
    return out.returncode == 0, log


def load_provenance(run: Path) -> dict:
    """Parse dvc.lock -> {stage: [(dep_path, md5_prefix), ...]}. Soft-fails without yaml."""
    lock = run / "dvc.lock"
    if not lock.is_file():
        return {}
    try:
        import yaml  # ships with dvc
        data = yaml.safe_load(lock.read_text()) or {}
    except Exception:
        return {}
    prov = {}
    for stage, body in (data.get("stages") or {}).items():
        deps = body.get("deps") or []
        prov[stage] = [(d.get("path"), (d.get("md5") or "")[:8]) for d in deps]
    return prov


def read_metric(run: Path, cid: str):
    f = run / "metrics" / f"{cid}.json"
    if not f.is_file():
        return None
    try:
        return json.loads(f.read_text()).get("value")
    except Exception:
        return None


def check_data(run: Path, cid: str, value: str, prov: dict):
    produced = read_metric(run, cid)
    if produced is None:
        return False, f"no metric metrics/{cid}.json (is there a dvc stage '{cid}'?)", ""
    pv, cv = as_num(produced), as_num(value)
    if pv is not None and cv is not None:
        ok = abs(pv - cv) <= max(abs(cv) * 0.01, 1e-9)
    else:
        ok = norm(str(produced)) == norm(value)
    detail = f"claimed {value} vs produced {produced}" + ("" if ok else "  <-- MISMATCH")
    trail = "; ".join(f"{p}@{h}" for p, h in prov.get(cid, []) if p)
    return ok, detail, trail


def fetch_text(url: str) -> tuple[str | None, str]:
    """Fetch a URL and return (plain_text|None, note). Best-effort, browser UA, HTML stripped."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PaperGraph audit)"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read(3_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
    except Exception as e:
        return None, f"fetch failed: {type(e).__name__}"
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", text))
    return text, "fetched"


def verify_source_url(url: str, quote: str) -> tuple[str, str]:
    """Return (mark, detail): ✅ quote at URL, ⚠️ not confirmed (page changed/blocked/JS)."""
    text, note = fetch_text(url)
    if text is None:
        return "⚠️", note
    return ("✅", "quote confirmed at URL") if norm(quote) in norm(text) \
        else ("⚠️", "quote not found in fetched page (may be paywalled/JS-rendered/changed)")


def check_source(run: Path, cid: str, quote: str):
    src = run / "sources" / f"{cid}.txt"
    if not src.is_file():
        return False, f"no source sources/{cid}.txt", ""
    ok = norm(quote) in norm(src.read_text(encoding="utf-8", errors="replace"))
    return ok, ("quote found verbatim" if ok else "quote NOT in source  <-- MISMATCH"), ""


def main(run_arg: str, verify_sources: bool = False):
    run = Path(run_arg).resolve()
    ledger = run / "claims.tsv"
    if not ledger.is_file():
        print(f"no claims.tsv in {run}"); sys.exit(2)
    rows = [l.split("\t") for l in ledger.read_text().splitlines() if l.strip()]
    header, data = rows[0], rows[1:]
    col = {name: i for i, name in enumerate(header)}
    has_data = any(r[col["kind"]] == "data" for r in data)

    repro_ok, repro_log = (None, "")
    if has_data:
        repro_ok, repro_log = dvc_repro(run)
    prov = load_provenance(run)

    results, passed = [], 0
    for r in data:
        cid, kind, value = r[col["claim_id"]], r[col["kind"]], r[col["value"]]
        if kind == "data":
            ok, detail, trail = check_data(run, cid, value, prov)
        elif kind == "source":
            ok, detail, trail = check_source(run, cid, value)
        else:
            ok, detail, trail = False, f"unknown kind {kind!r}", ""
        passed += ok
        results.append((cid, kind, ok, detail, trail))
    rate = passed / len(data) if data else 0.0

    lines = ["## RIGOR gate", ""]
    if has_data:
        lines.append(f"dvc repro: **{'ok' if repro_ok else 'FAILED'}** (re-executed all data "
                     f"transforms from raw data)")
        if not repro_ok:
            lines += ["", "```", repro_log[-600:], "```"]
        lines.append("")
    lines += [f"reproduce-rate: **{passed}/{len(data)} = {rate:.0%}**  "
              f"{'PASS ✅' if rate == 1.0 else 'FAIL ❌'}", ""]
    for cid, kind, ok, detail, trail in results:
        line = f"- {'✅' if ok else '❌'} `{cid}` ({kind}): {detail}"
        if trail:
            line += f"\n    - provenance: {trail}"
        lines.append(line)

    if verify_sources:
        src_rows = [r for r in data if r[col["kind"]] == "source"]
        lines += ["", "### source-URL audit (networked, non-fatal)"]
        if not src_rows:
            lines.append("- (no kind=source claims)")
        for r in src_rows:
            cid, url, quote = r[col["claim_id"]], r[col["raw_ref"]], r[col["value"]]
            mark, detail = verify_source_url(url, quote)
            lines.append(f"- {mark} `{cid}`: {detail} — {url}")

    report = run / "gate_report.md"
    prev = report.read_text() if report.is_file() else ""
    prev = re.split(r"(?m)^## RIGOR gate$.*?(?=^## |\Z)", prev, flags=re.S)
    head = "".join(prev).rstrip()
    report.write_text((head + "\n\n" if head else "") + "\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(0 if rate == 1.0 else 1)


if __name__ == "__main__":
    argv = sys.argv[1:]
    verify = "--verify-sources" in argv
    positional = [a for a in argv if not a.startswith("--")]
    main(positional[0] if positional else ".", verify_sources=verify)
