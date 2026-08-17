"""Aggregate mechanical scoring across the 5-topic × 3-mode ablation v2.

Reuses the SAME per-run metrics as the v1 run (score.py / fidelity.py) so numbers
are directly comparable, then aggregates by mode across all topics. Layout:
runs/T{1..5}/{raw,skills,tree}/ . Prints a per-topic table + a by-mode mean.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from score import score_run
from fidelity import check as fidelity_check

MODES = ("raw", "skills", "tree")
TOPICS = ("T1", "T2", "T3", "T4", "T5")


def collect(base: Path) -> dict:
    rows = {}  # (topic, mode) -> merged metrics
    for t in TOPICS:
        for m in MODES:
            run = base / "runs" / t / m
            if not (run / "article.md").is_file():
                continue
            s = score_run(run, m)
            f = fidelity_check(m, run)
            rows[(t, m)] = {**s, **{f"fid_{k}": v for k, v in f.items()
                                    if k not in ("mode", "error")}}
    return rows


def mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(sum(xs) / len(xs), 2) if xs else None


def by_mode(rows: dict) -> dict:
    agg = {}
    fields = ("words", "citations_inline", "distinct_sources", "traceable_sources",
              "traceability", "cited_source_bytes", "adversarial_hits",
              "fid_english_quotes", "fid_verbatim_in_sources", "fid_fidelity")
    for m in MODES:
        vals = [v for (t, mm), v in rows.items() if mm == m]
        agg[m] = {"n_topics": len(vals)}
        for fld in fields:
            agg[m][fld] = mean([v.get(fld) for v in vals])
    return agg


def main(base: str) -> None:
    base = Path(base)
    rows = collect(base)
    out = {
        "per_run": {f"{t}/{m}": rows[(t, m)] for (t, m) in sorted(rows)},
        "by_mode_mean": by_mode(rows),
        "coverage": {t: [m for m in MODES if (t, m) in rows] for t in TOPICS},
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
