#!/usr/bin/env python3
"""Prove the safety tests kill two required control mutations."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType


SKILL_ROOT = Path(__file__).resolve().parents[1]
EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_ROOT))


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load mutation module {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _mutated_module(source_path: Path, needle: str, replacement: str, name: str, directory: Path) -> ModuleType:
    source = source_path.read_text(encoding="utf-8")
    if source.count(needle) != 1:
        raise AssertionError(f"mutation anchor count changed for {source_path.name}")
    target = directory / source_path.name
    target.write_text(source.replace(needle, replacement), encoding="utf-8")
    return _load(name, target)


def mutation_signed_body_guard() -> None:
    with tempfile.TemporaryDirectory() as td:
        mutant = _mutated_module(
            SKILL_ROOT / "scripts" / "ocr_ingest.py",
            "if transmitted_body != signed_body or expected_hash != _sha256(transmitted_body):",
            "if False:",
            "papergraph_mutant_ocr",
            Path(td),
        )
        harness = _load("papergraph_mutation_harness_signing", EVALS / "run_all.py")
        harness.ocr_ingest = mutant
        try:
            harness.test_tc3_mutation_rejected_before_send()
        except AssertionError:
            return
        raise AssertionError("signed-body test survived a removed mismatch guard")


def mutation_eval_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as td:
        mutant = _mutated_module(
            SKILL_ROOT / "scripts" / "validate_eval_bundle.py",
            'return _result("INCOMPLETE", complete=False, reasons=[f"missing:{name}" for name in missing])',
            'return _result("SHIP", complete=True, reasons=[])',
            "papergraph_mutant_eval",
            Path(td),
        )
        harness = _load("papergraph_mutation_harness_eval", EVALS / "run_all.py")
        harness.validate_eval_bundle = mutant
        try:
            harness.test_eval_missing_each_required_input_never_ship()
        except AssertionError:
            return
        raise AssertionError("missing-input test survived a removed fail-closed verdict")


def main() -> int:
    checks = [
        ("mutation_signed_body_guard", mutation_signed_body_guard),
        ("mutation_eval_fail_closed", mutation_eval_fail_closed),
    ]
    killed = 0
    for name, check in checks:
        try:
            check()
        except Exception as exc:
            print(f"FAIL {name}: {type(exc).__name__}")
        else:
            killed += 1
            print(f"PASS {name}")
    print(f"MUTATION_SCORE {killed}/{len(checks)}")
    print(f"RESULT {'PASS' if killed == len(checks) else 'FAIL'}")
    return 0 if killed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
