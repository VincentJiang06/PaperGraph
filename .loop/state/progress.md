# Progress — PaperGraph v1 build

Resume point after any compaction/crash: re-read this file + contract.md + log.md.
Do NOT trust a session summary.

## Loop status
- Outer budget: 3 re-entries. Used: 0.
- Current stage: **m2-docs** (attempt 1, cap 3). [m0 PASSED; m1 PASSED attempt 2]
- Gate tags: gate/m0-foundation, gate/m1-proof-loop.
- m0: 171 green; evaluator PASS. A1–A7, A24.
- m1: 312 green; attempt1 FAIL (F1 hollow replay) → attempt2 fix (genuine replay
  via CommitDecision record payloads + V-EDGE-02 wired) → evaluator PASS.
  A8–A15 proven. Doc-syncs: docs/08 §2b record field, B6 bridge edge_claim,
  docs/07 proof/.lock. The loop caught + closed a real green-but-hollow check.

## m1 attempt-2 fix plan (F1 + secondary)
F1: replay_reproduces is tautological (slices post lines, ignores action content).
  Fix = make CommitDecision actions carry the full appended/updated record, and
  rewrite replay to reconstruct post-state from ONLY (pre-state + actions), then
  compare to actual post-state — so a corrupted action → False. Add the adversarial
  test (corrupt an action target → replay returns False) to prove non-tautology.
  DOC-SYNC: docs/08 §2b CommitDecision action payload carries the record.
Secondary (evaluator): V-EDGE-02 registered but dead (never run at commit) → wire
  it into commit-time graph validation + fixture.
Also apply the 2 accepted DOC-SYNCs from attempt1: bridge edge_claim text in
  docs/08 B6; proof/.results.lock in docs/07 layout + Validator note.
Constraint: do NOT regress the sound parts; re-green determinism goldens (actions
  now larger — CommitDecision byte-identity + S1/S4 must still hold).

## Carried-forward notes for M1 (from m0 evaluator/generator)
- golden scope.period "2020–2023, centered on…" is NOT a parseable year range →
  scope_compatible (V-NODE-03) will fall back to substring matching. Expected per
  docs/01 P6 verbatim copy; M1 committer must handle this gracefully (it does by
  the §0 fallback). No action needed, awareness only.
- CLI stub surface already registered for all 43 commands; M1 replaces the proof/
  queue/expand/validate/commit group stubs with real behavior.
- textutil, ids, clock, serializer, store, snapshot, schemas (all *.v1) are DONE
  and available to import — M1 builds on them, does not re-create them.
- docs edited during m0 (doc-first): docs/09 §0 stoplist "72"→"82"; docs/10 §4
  added --help exemption note. Both shipped in the m0 commit.

## Architecture in use
- Orchestrator (main, Opus) = planner + loop driver; stays lean.
- Generator subagent (Opus, high) builds each milestone's src+tests.
- Evaluator subagent (Opus, high, FRESH each gate) adversarially gates.
- Env: `.venv` (uv, CPython 3.12.13). Gate via `.venv/bin/python -m pytest -q`.

## Stage plan — m0-foundation
Deliverables (docs/10 §3 layout, §7 M0; docs/11 §9 M0 row; contract A1–A7):
- `pyproject.toml` (deps + `[project.scripts] paperproof=paperproof.cli.app:main`, requires-python>=3.12)
- `src/paperproof/schemas/` — ALL *.v1 models + registry (schema_version→class); extra=forbid
- `src/paperproof/textutil.py` — docs/09 §0 exactly (the ONLY tokenizer/counter)
- `src/paperproof/ids.py`, `clock.py` (PAPERPROOF_NOW), canonical serializer
- `src/paperproof/store/jsonl.py` (append/latest_by_id/fcntl/path-safety), `snapshot.py`
- `src/paperproof/scoping/` — topic parser P1–P7 → PaperSpec + Contract; spec build/accept/show
- `src/paperproof/validate/registry.py` + `rules/v_spec.py`, `v_path.py`
- `src/paperproof/cli/` — typer app, FULL closed surface (docs/10 §4); M0 cmds real,
  rest = stub {ok:false, errors:["NOT-IMPLEMENTED"]} exit 1; one JSON envelope always
- tests: unit/{textutil,jsonl_store,snapshot,ids}, contract/{schemas,v_spec,v_path,cli_envelope}
- tests/conftest.py — determinism harness (clock/pp/project/canonical fixtures, docs/11 §3)
- fixtures/{schemas,topics,vrules/V-SPEC-*,V-PATH-*}
Build order: textutil+ids+clock FIRST, then schemas, store, scoping, validate, cli.
Gate: the m0 `feedback_signal.check` (pytest -q + 8 file-presence tests).

## Next actions (M2 — docs)
Deliverables: docsdb/ (ingest + content_hash dedup, text extraction, matcher
[§0 tokens, score≥2 + scope_compatible], request fingerprint cache, DocsPack
builder), V-DR rules (V-DR-01..06 incl. quote_match), docs CLI (ingest/search/
build-pack/request/ingest-result), needs_docs loop wiring in committer (cache
check, born-dead at cap 2). Make real the docs group + any commit paths for
docs verdicts. Tests: test_v_dr (D01–D05 hostiles + quote_match), S2 (cache +
born-dead cap), S3 (contradiction cascade — its contradicted verdict needs a
non-empty DocsPack, hence M2). Gate = m2 feedback_signal.check; on_failure=restart (cap 3).
Provides for M2: schemas (document/evidence_unit/docs_request/docs_result all
exist), textutil scope_compatible/quote_match/tokens DONE, committer needs_docs
verdict path exists (docs/08 B6 row) — M2 wires the DocsRequest creation + cache.
1. dispatch M2 generator (Opus/high): emphasize matcher determinism, content_hash
   dedup, request fingerprint cache (no work item on hit), quote_match at ingest,
   born-dead cap at 2, S3 cascade + verify.
2. run M2 gate → gate-reports/m2-docs-attempt1.md.
3. fresh evaluator (probe: cache-hit truly creates NO work item; quote_match
   rejects fabricated quotes; born-dead cap; S3 cascade tombstones + cancels).
4. on PASS: git tag gate/m2-docs, commit, advance to m3.

## Open doc issues found during build
(none yet)
