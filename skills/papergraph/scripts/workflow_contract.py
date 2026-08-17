#!/usr/bin/env python3
"""Offline executable contract for the minimal PaperGraph artifact flow."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from scripts import ocr_ingest, validate_eval_bundle


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run_offline_smoke(
    *,
    topic: str,
    response_path: str | Path,
    eval_bundle_dir: str | Path,
    output_dir: str | Path,
    image_width: int,
    image_height: int,
    provider_run_id: str,
    source_id: str,
    gate_runner: Callable[[Path], Mapping[str, str]],
) -> dict[str, Any]:
    """Create the minimal durable artifacts and apply both release layers."""

    if not topic.strip():
        raise ValueError("topic is required")
    output = Path(output_dir)
    replay = ocr_ingest.replay_response(
        response_path,
        output / "sources",
        image_width=image_width,
        image_height=image_height,
        provider_run_id=provider_run_id,
        source_id=source_id,
    )
    first_element = replay["source"]["elements"][0] if replay["source"]["elements"] else None
    source_excerpt = first_element["text"] if first_element else ""
    _atomic_text(
        output / "positions.md",
        "## P1: Primary thesis\n"
        "holder: Working literature\n"
        f"claim: The evidence relevant to {topic} supports a conditional thesis.\n"
        "rests_on: Archived source observations\n\n"
        "## STRONGEST-OBJECTION\n"
        "claim: The available sources may not establish external validity.\n"
        "rests_on: Broader evidence would materially narrow the thesis.\n",
    )
    _atomic_text(
        output / "claims.tsv",
        "claim_id\tkind\tclaim_text\tvalue\traw_ref\ttransform_or_source\treproduced\n"
        f"C1\tsource\tArchived OCR source observation\t{source_excerpt}\tlocal:{source_id}\t"
        "sources/source.txt\ttrue\n",
    )
    _atomic_text(
        output / "paper.md",
        f"field-weight: mixed\n\n# {topic}\n\n"
        "[P1] This offline smoke artifact records the mapped thesis and links its empirical "
        "observation to C1. It is a contract fixture, not a substitute for the native-agent author wave.\n\n"
        "[OBJ] External validity remains the strongest objection and must be tested against broader sources.\n",
    )

    gate_results = dict(gate_runner(output))
    gate_ok = gate_results == {"divergence": "PASS", "rigor": "PASS"}
    _atomic_text(
        output / "gate_report.md",
        "# Gate report\n\n"
        f"- divergence: {gate_results.get('divergence', 'MISSING')}\n"
        f"- rigor: {gate_results.get('rigor', 'MISSING')}\n",
    )
    eval_result = validate_eval_bundle.validate_bundle(eval_bundle_dir)
    _atomic_text(
        output / "eval_verdict.json",
        json.dumps(eval_result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )
    verdict = "SHIP" if gate_ok and eval_result["verdict"] == "SHIP" else "REVISE"
    return {
        "verdict": verdict,
        "gate_results": gate_results,
        "eval_verdict": eval_result["verdict"],
        "source_traceability_rate": 1.0 if first_element else 0.0,
        "artifacts": sorted(str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()),
    }


if __name__ == "__main__":
    raise SystemExit("workflow_contract is an import-only offline contract; use evals/run_all.py")
