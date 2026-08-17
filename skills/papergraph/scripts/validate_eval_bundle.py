#!/usr/bin/env python3
"""Fail-closed validator for PaperGraph's held-out D1-D5 bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


REQUIRED_FILES = (
    "d1_answer_key.json",
    "d2_steelmans.json",
    "d3_adversary.json",
    "d4b_claim_audit.json",
    "d5_referees.json",
)


def _result(verdict: str, *, complete: bool, reasons: list[str]) -> dict[str, Any]:
    return {"verdict": verdict, "complete": complete, "reasons": sorted(set(reasons))}


def _load(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.name}: unreadable JSON") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"{path.name}: root must be an object")
    return value


def validate_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    """Return SHIP only for a complete and internally conforming held-out panel."""

    root = Path(bundle_dir)
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        return _result("INCOMPLETE", complete=False, reasons=[f"missing:{name}" for name in missing])

    try:
        d1, d2, d3, d4, d5 = (_load(root / name) for name in REQUIRED_FILES)
    except ValueError as exc:
        return _result("INCOMPLETE", complete=False, reasons=[str(exc)])

    reasons: list[str] = []
    positions = d1.get("positions")
    if d1.get("dimension") != "D1" or not isinstance(positions, list) or not positions:
        reasons.append("D1 answer key is incomplete")
        position_ids: set[str] = set()
    else:
        position_ids = set()
        for index, position in enumerate(positions):
            if not isinstance(position, Mapping):
                reasons.append(f"D1 position {index} is malformed")
                continue
            position_id = position.get("position_id")
            answer = position.get("literature_answer")
            if not isinstance(position_id, str) or not position_id or not isinstance(answer, str) or not answer:
                reasons.append(f"D1 position {index} lacks a literature answer")
            elif position_id in position_ids:
                reasons.append(f"D1 duplicate position:{position_id}")
            else:
                position_ids.add(position_id)

    steelmans = d2.get("steelmans")
    if d2.get("dimension") != "D2" or not isinstance(steelmans, Mapping):
        reasons.append("D2 steelman map is incomplete")
    else:
        if set(steelmans) != position_ids:
            reasons.append("D2 does not cover exactly the D1 positions")
        for position_id, judgment in steelmans.items():
            if not isinstance(judgment, Mapping) or judgment.get("passed") is not True:
                reasons.append(f"D2 steelman failed:{position_id}")

    if (
        d3.get("dimension") != "D3"
        or d3.get("objection_robustness") != "PASS"
        or d3.get("stronger_unaddressed_objection") is not False
    ):
        reasons.append("D3 objection robustness failed")

    honesty_flags = d4.get("honesty_flags")
    traceability = d4.get("traceability_rate")
    if d4.get("dimension") != "D4b" or d4.get("claims_complete") is not True:
        reasons.append("D4b claim audit is incomplete")
    if not isinstance(traceability, (int, float)) or isinstance(traceability, bool) or traceability != 1.0:
        reasons.append("D4b traceability rate is below 1.0")
    if not isinstance(honesty_flags, list) or honesty_flags:
        reasons.append("D4b has unresolved honesty flags")

    referees = d5.get("referees")
    passing_band = d5.get("passing_band")
    if d5.get("dimension") != "D5" or not isinstance(referees, list) or len(referees) < 3:
        reasons.append("D5 requires at least three referees")
    else:
        referee_ids: set[str] = set()
        for referee in referees:
            if not isinstance(referee, Mapping):
                reasons.append("D5 referee is malformed")
                continue
            referee_id = referee.get("referee_id")
            if not isinstance(referee_id, str) or not referee_id or referee_id in referee_ids:
                reasons.append("D5 referee IDs must be unique")
            else:
                referee_ids.add(referee_id)
            if referee.get("independent") is not True:
                reasons.append(f"D5 referee is not independent:{referee_id}")
            if passing_band not in {"ACCEPT", "MAJOR_REVISION"} or referee.get("band") != passing_band:
                reasons.append(f"D5 referee is outside the passing band:{referee_id}")

    return _result("REVISE" if reasons else "SHIP", complete=True, reasons=reasons)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a PaperGraph held-out evaluation bundle")
    parser.add_argument("bundle_dir")
    args = parser.parse_args(argv)
    result = validate_bundle(args.bundle_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "SHIP" else 1


if __name__ == "__main__":
    raise SystemExit(main())
