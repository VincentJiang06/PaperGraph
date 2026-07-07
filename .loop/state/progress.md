# Progress — PaperGraph v1 build

Resume point after any compaction/crash: re-read this file + contract.md + log.md.
Do NOT trust a session summary.

## Loop status — COMPLETE
- All milestones gated, committed, tagged, pushed. Automated definition-of-done MET.
- Gate tags: gate/m0-foundation, gate/m1-proof-loop, gate/m2-docs, gate/m3-endgame, gate/m4-surface.
- Final state: 381 tests green from a FRESH CLONE in a clean 3.12 venv; wheel builds
  and ships prompts + ui/static (real cytoscape). paperproof verify genuinely catches
  corruption. All 27 contract assertions: A1-A25 machine-proven; A26 (live smoke, real
  Claude workers) + A27 (doc-first, spot-audited clean bar one reconciled finding) are
  the deliberate human nodes.
- Per-milestone: m0 PASS(171) · m1 PASS attempt2(312, fixed hollow replay) · m2 PASS(335)
  · m3 PASS(367, +N1 verify crossref) · m4 PASS(375→377, real cytoscape) · final-audit
  PASS (fresh-clone caught+fixed the .gitignore db/ packaging bug) · polish(381, 4 low
  findings closed).
- The loop caught 3 things a self-grading build would have shipped: a tautological
  V-COMMIT-04 replay (m1), a verify/doc crossref gap (m3-N1), and a .gitignore that
  silently excluded the whole M4 db package from every commit (final-audit fresh-clone).

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

## Next actions (M3 — endgame)
Deliverables: freeze/ (closures local/subtree/spine, V-FRZ-01..04, language-limit
union, FreezeItem, batch-commit set_frozen, unfreeze re-open), compiler/ (dry-run:
section-plan template single_event_mechanism + 5 gap kinds + writing_ready +
V-CDR idempotency/auto-cancel; draft-map determinism; prose ingest V-PROSE),
audit/ (mechanical binding/strength/scope/coverage), trace walker
(sentence->evidence->raw), graph msa-check MSA-1..9. Make real: freeze/compiler/
audit groups + msa-check + trace. Tests: test_v_frz, test_v_cdr, test_v_prose_aud,
S7 (full P4: msa green->spine freeze->zero-gap dry run->draft-map->prose->ingest->
audit passed; trace resolves every spine node; MSA-1..9 individually), S1 freeze
coda, S3 MSA-9 coda (hollowed spine fails MSA-9). Gate=m3 check; on_failure=restart (cap 3).
Provides: committer freeze_batch/unfreeze_batch kinds exist; CompileWorker prompt
shipped (M0); spine walker + MSA model (M1 graph/); add FakeCompileWorker.
1. dispatch M3 generator (Opus/high): zero-gap-by-construction dry run (docs/06
   reachability note) + gap machinery still tested via V-CDR fixtures; MSA-9
   vacuous-spine guard; trace chain end-to-end; annotation grammar V-PROSE; S7
   asserts MSA-1..9 individually + audit passed + trace.
2. run M3 gate -> gate-reports/m3-endgame-attempt1.md.
3. fresh evaluator (probe: dry run zero-gap after clean freeze BUT each gap kind
   caught by a V-CDR fixture; MSA-9 fails on hollowed spine; trace to raw file;
   annotation grammar rejects mangled prose; audit catches seeded forbidden-language).
4. on PASS: git tag gate/m3-endgame, commit, advance to m4.

## Open doc issues found during build
(none yet)
