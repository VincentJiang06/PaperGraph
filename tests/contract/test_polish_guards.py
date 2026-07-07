"""Guard tests for the v1 polish pass (final-audit low-severity findings).

Each test pins a doc-first correction so the fixed behaviour cannot silently
regress:

  F1  commit_queue derived view is FIFO by validation time (docs/05 §Queues),
      not by work_item_id — asserted for BOTH the CLI (queue/commands.py) and
      the WebUI read-model (ui/readmodel.py).
  F2  the built wheel ships the package data (prompts/*.txt + ui/static/**)
      that the runtime loads (pyproject packaging).
  F3  trace's claim-annotation match tolerates "(claim:NODE-xxx)" (no space),
      matching the writers' regex (compiler/prose.py, audit/run.py).
  F4  a text-less ingest-result Document has text_path=null and no empty text
      file on disk (docs/04).
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from paperproof.graph import trace
from paperproof.prooftask import builder
from paperproof.queue import commands, engine
from paperproof.store import jsonl
from paperproof.ui import readmodel

from tests.fakes import scenario
from tests.fakes.workers import FakeDocsWorker, FakeProofWorker, drain_docs, prove_one

pytestmark = pytest.mark.contract


# --- F1: commit_queue FIFO by validation time -------------------------------


class _ListReader:
    """Minimal IndexReader stand-in: readmodel.queue only reads work_items."""

    def __init__(self, items: list[dict]) -> None:
        self._items = items

    def current(self, table: str) -> list[dict]:
        return self._items if table == "work_items" else []


def _drive_to_validated(paths, wi_id: str) -> None:
    """claim -> (touch outputs) -> complete -> validate_pass at the current clock."""
    engine.claim(paths, queue_name="proof_queue", agent="w", wi_id=wi_id)
    for out in engine.get_item(paths, wi_id).get("output_files", []):
        p = paths.project_dir / out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")
    engine.complete(paths, wi_id)
    engine.validate_pass(paths, wi_id)


def test_commit_queue_is_fifo_by_validation_time(project, pp, clock):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_layer0(paths)
    builder.build_frontier(paths)
    engine.run_sweeps(paths, "test")

    proof_items = {
        i["target_id"]: i["work_item_id"]
        for i in engine.load_items(paths)
        if i["queue_name"] == "proof_queue"
    }
    lo, hi = sorted([proof_items[scenario.A], proof_items[scenario.B]])

    # Validate the HIGHER work_item_id FIRST (earlier validation time), then the
    # LOWER id at a later clock tick: validation-time order is the reverse of
    # id order, so the two orderings are distinguishable.
    clock.tick()
    _drive_to_validated(paths, hi)
    clock.tick()
    _drive_to_validated(paths, lo)

    # CLI derived view (queue/commands.py).
    cli_order = [i["work_item_id"] for i in commands.list_items(paths, queue="commit_queue")["items"]]
    assert cli_order == [hi, lo], "commit_queue must be FIFO by validation time, not work_item_id"

    # WebUI read-model derived view (ui/readmodel.py) mirrors the same order.
    rm = readmodel.queue(_ListReader(engine.load_items(paths)), "commit_queue")
    assert [i["work_item_id"] for i in rm["items"]] == [hi, lo]


# --- F2: the wheel ships package data ---------------------------------------


@pytest.mark.slow
def test_wheel_ships_prompts_and_ui_static(tmp_path):
    if shutil.which("uv") is None:  # pragma: no cover - environment guard
        pytest.skip("uv not on PATH")
    repo = Path(__file__).resolve().parents[2]
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=repo, check=True, capture_output=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    names = set(zipfile.ZipFile(wheel).namelist())
    required = {
        "paperproof/prompts/proof_worker.txt",
        "paperproof/prompts/docs_worker.txt",
        "paperproof/prompts/compile_worker.txt",
        "paperproof/prompts/retry_suffix.txt",
        "paperproof/ui/static/index.html",
        "paperproof/ui/static/vendor/cytoscape.min.js",
    }
    missing = required - names
    assert not missing, f"wheel is missing package data: {sorted(missing)}"


# --- F3: trace tolerates a no-space claim annotation ------------------------


def test_trace_finds_no_space_claim_annotation(project, pp):
    paths = scenario.paths_for_pp(pp)
    prose_dir = paths.resolve("compiler/prose")
    prose_dir.mkdir(parents=True, exist_ok=True)
    # No space after the colon: valid to the writers' \(claim:\s*NODE-\d+\s*\).
    (prose_dir / "s1-intro.md").write_text(
        "The transmission mechanism holds (claim:NODE-001).", encoding="utf-8"
    )
    occ = trace._prose_occurrences(paths, "NODE-001")
    assert occ == [{"section": "s1-intro", "sentence": 1}]


# --- F4: text-less ingest-result Document has null text_path ----------------


def test_ingest_result_textless_doc_has_null_text_path(project, pp):
    paths = scenario.paths_for_pp(pp)
    scenario.seed_docs_facts(paths, [scenario.FACT_CLAIM])

    # Drive NODE-003 to needs_docs so a DocsRequest + docs work item exist.
    proof_worker = FakeProofWorker({"NODE-003": scenario.node_insufficient_form()})
    prove_one(paths, "NODE-003", proof_worker)

    # A fulfilling DocsResult whose single document carries no text. A web
    # document must include inline text (V-DR-04), so the text-less case is a
    # user_provided-origin document with no evidence units.
    spec = {
        "documents": [
            {
                "title": "Analyst desk notes",
                "source_type": "user_notes",
                "origin": {"kind": "user_provided", "path": "docs/raw/desk-notes.txt", "url": None},
                "citation_key": "DeskNotes",
                "text": None,
            }
        ],
        "evidence_units": [],
        "not_found": False,
        "search_log": ["scripted desk-notes lookup"],
    }
    drain_docs(paths, FakeDocsWorker({"*": spec}))

    docs = jsonl.latest_records(paths.resolve("docs/documents.jsonl"), "doc_id")
    doc = next(d for d in docs if d["citation_key"] == "DeskNotes")
    assert doc["text_path"] is None, "text-less document must have text_path=null (docs/04)"
    assert not (paths.project_dir / f"docs/text/{doc['doc_id']}.txt").exists(), (
        "no empty text file should be written for a text-less document"
    )
