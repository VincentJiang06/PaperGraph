#!/usr/bin/env python3
"""Deterministic precision/recall gate for PaperGraph trigger routing."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from scripts.trigger_policy import classify_request  # noqa: E402


def _metrics(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    true_positive = sum(row["expected"] and row["actual"] for row in rows)
    false_positive = sum(not row["expected"] and row["actual"] for row in rows)
    false_negative = sum(row["expected"] and not row["actual"] for row in rows)
    true_negative = sum(not row["expected"] and not row["actual"] for row in rows)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
        "tn": true_negative,
        "total": len(rows),
    }


def main() -> int:
    fixture = json.loads((Path(__file__).with_name("trigger_cases.json")).read_text(encoding="utf-8"))
    cases = fixture["cases"]
    threshold = float(fixture["threshold"])
    positives = sum(case["should_trigger"] for case in cases)
    holdout_cases = [case for case in cases if case.get("holdout") is True]
    if len(cases) < 20 or positives * 2 != len(cases) or len(holdout_cases) / len(cases) < 0.4:
        print("FAIL trigger_fixture_contract")
        return 1

    rows: list[dict[str, Any]] = []
    failures = 0
    for case in cases:
        actual = classify_request(case["prompt"]).get("activate") is True
        expected = case["should_trigger"] is True
        row = {"id": case["id"], "expected": expected, "actual": actual, "holdout": case.get("holdout") is True}
        rows.append(row)
        if actual == expected:
            print(f"PASS {case['id']}")
        else:
            failures += 1
            print(f"FAIL {case['id']} expected={str(expected).lower()} actual={str(actual).lower()}")

    overall = _metrics(rows)
    holdout = _metrics([row for row in rows if row["holdout"]])
    holdout_positives = sum(row["expected"] for row in rows if row["holdout"])
    holdout_negatives = len(holdout_cases) - holdout_positives
    gated = all(
        value >= threshold
        for value in (overall["precision"], overall["recall"], holdout["precision"], holdout["recall"])
    )
    print(
        "METRICS "
        + json.dumps(
            {
                "balanced": positives * 2 == len(cases),
                "cases": len(cases),
                "holdout_cases": len(holdout_cases),
                "holdout_fraction": round(len(holdout_cases) / len(cases), 6),
                "holdout_positive": holdout_positives,
                "holdout_negative": holdout_negatives,
                "overall": overall,
                "holdout": holdout,
                "threshold": threshold,
            },
            sort_keys=True,
        )
    )
    print(f"RESULT {'PASS' if failures == 0 and gated else 'FAIL'}")
    return 0 if failures == 0 and gated else 1


if __name__ == "__main__":
    raise SystemExit(main())
