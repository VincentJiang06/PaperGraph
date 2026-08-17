"""Aggregate the blind judge panel. Reads blinded/KEY.json (slot->mode) and
blinded/scores/judge-*.json (slot scores per topic per judge), un-blinds, and
computes: per-topic per-mode mean across judges, and the overall by-mode mean
across topics. Dimensions + overall. Prints JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

DIMS = ("structure_logic", "evidence_quality", "adversarial_rigor",
        "calibration", "overall")
MODES = ("raw", "skills", "tree")


def mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(sum(xs) / len(xs), 2) if xs else None


def main(base: str = ".") -> None:
    base = Path(base)
    key = json.loads((base / "blinded" / "KEY.json").read_text())
    judges = sorted((base / "blinded" / "scores").glob("judge-*.json"))
    panels = [json.loads(p.read_text()) for p in judges]

    # collect: (topic, mode, dim) -> [scores across judges]
    cell = {}
    for topic, slotmap in key.items():
        for slot, mode in slotmap.items():
            mode = mode.replace(" (MISSING)", "")
            for panel in panels:
                rec = panel.get(topic, {}).get(slot)
                if not rec:
                    continue
                for d in DIMS:
                    cell.setdefault((topic, mode, d), []).append(rec.get(d))

    per_topic = {}
    for topic in key:
        per_topic[topic] = {m: {d: mean(cell.get((topic, m, d), [])) for d in DIMS}
                            for m in MODES}

    by_mode = {}
    for m in MODES:
        by_mode[m] = {}
        for d in DIMS:
            vals = [per_topic[t][m][d] for t in key if per_topic[t][m][d] is not None]
            by_mode[m][d] = mean(vals)

    out = {"n_judges": len(judges), "per_topic": per_topic, "by_mode_mean": by_mode}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
