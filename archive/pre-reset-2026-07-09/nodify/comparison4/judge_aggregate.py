"""Aggregate the blind judge panel for the aggressive-research eval. Reads
blinded/KEY.json (slot->arm) and blinded/scores/judge-*.json, un-blinds, and computes
per-topic per-arm means across judges + an overall by-arm mean. 2 arms (tree, notree),
investigation-quality dimensions. Prints JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

DIMS = ("coverage", "depth", "adversarial_completeness", "grounding",
        "convergence", "calibration")
ARMS = ("tree", "notree")


def mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(sum(xs) / len(xs), 2) if xs else None


def main(base: str = "."):
    base = Path(base)
    key = json.loads((base / "blinded" / "KEY.json").read_text())
    panels = [json.loads(p.read_text())
              for p in sorted((base / "blinded" / "scores").glob("judge-*.json"))]

    cell = {}  # (topic, arm, dim) -> [scores]
    for topic, slotmap in key.items():
        for slot, arm in slotmap.items():
            arm = arm.replace(" (MISSING)", "")
            for panel in panels:
                rec = panel.get(topic, {}).get(slot)
                if not rec:
                    continue
                for d in DIMS:
                    cell.setdefault((topic, arm, d), []).append(rec.get(d))

    per_topic = {t: {a: {d: mean(cell.get((t, a, d), [])) for d in DIMS} for a in ARMS}
                 for t in key}
    by_arm = {}
    for a in ARMS:
        by_arm[a] = {}
        for d in DIMS:
            vals = [per_topic[t][a][d] for t in key if per_topic[t][a][d] is not None]
            by_arm[a][d] = mean(vals)
        # composite = mean of the six dimension means
        dvals = [by_arm[a][d] for d in DIMS if by_arm[a][d] is not None]
        by_arm[a]["composite"] = round(sum(dvals) / len(dvals), 2) if dvals else None

    out = {"n_judges": len(panels), "per_topic": per_topic, "by_arm_mean": by_arm}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
