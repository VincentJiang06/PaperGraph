# Progress — PaperGraph v1 build

Resume point after any compaction/crash: re-read this file + contract.md + log.md.
Do NOT trust a session summary.

## Loop status — stage m5-r3-behavior COMPLETE (2026-07-08), gate PASS
- ALL r3 worklist items now landed: r3-core (T-r3-1/2/3/6/8) + m5 (T-r3-4/5/7/9/10).
  Code has fully caught up to spec r3. Contract A28–A32 all [x] (gate PASS).
- m5 result: Generator 399 green (386 +13); fresh Evaluator PASS — 5 probes re-run
  independently, weakened-test audit clean, T-r3-7 docs-path judged sound. Evaluator
  found F1 (docs/05 stale on the docs implicit-complete path) → Orchestrator reconciled
  docs/05 §Validation Gate + complete row before tagging. Tag: gate/m5-r3-behavior.
- Spec-vs-code: NOW ALIGNED at r3. Next staged work = search program S1-S5 (docs/13-18,
  design-frozen) as the v1.1 milestone — adopt via a docs/00 changelog entry first.
- Roles: Orchestrator(me)=planner+driver; Generator subagent=impl; fresh Evaluator=gate.

## v1 loop status — COMPLETE (history)
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

## ACTIVE STAGE — m5-r3-behavior (the 5 deferred r3 behavior upgrades)
Pattern plan_execute_verify; cap 3; on_failure=restart-from-baseline. Gate = full
`pytest -q` green + V-SWEEP-01 in registry + test_v_sweep.py present. Grade A28–A32.
DONE already in r3-core (do NOT redo): T-r3-1/2/3/6/8 + T-r3-10 template blocks.

Build order (each item cites its authoritative doc; generator re-reads the doc,
never implements from memory — spec-drift guard):

1. T-r3-4  Evidence floor ≥2 EU from ≥2 DISTINCT documents. Bindings are evidence_ids;
   resolve each → EvidenceUnit.doc_id via docs/evidence_units.jsonl (shared helper).
   Sites: graph/commands.py MSA-4 (line ~114, `>=1` → floor); freeze/apply.py V-FRZ-02
   (line ~128, `<1` → floor); compiler/dry_run.py missing_evidence gap (docs/06 §85-86).
   ALL THREE must use ONE floor fn so they stay consistent (docs/06 reachability note).
   Fixtures: S7 lifted — its docs ingest yields ≥2 EU from ≥2 docs and node_sufficient_form
   binds both (tests/fakes/scenario.py S7_M ~line 320 binds ["EU-001"] today; DocsResult
   ~line 203 has one doc). NEW negative: a 1-binding (and a 2-EU-same-doc) spine node
   FAILS msa-check AND spine freeze. Docs: docs/02 MSA-4, docs/06 §85-96, docs/09 V-FRZ-02.

2. T-r3-5  V-SWEEP-01 (NEW rule). Register in validate/registry.py; new rule module
   validate/rules/v_sweep.py; enforced by expander/ingest.py on the FIRST proposal whose
   layer ≥ 1 ("beyond layer 0"). Floor per fact/mechanism LAYER-0 node N: (≥2 EU from ≥2
   docs REQUESTED-for-N, trace request→DRES→ingested_from — reuse docsdb/pack.py `_requested_eus`)
   OR (≥2 sweep DocsRequests targeting N with status=not_found). graph msa-check adds an
   INFORMATIONAL sweep-coverage line (not a pass/fail MSA item). Cover via SCENARIO_COVERED
   → test_v_sweep.py (refuse-then-pass). DOC-SYNC: "fact/mechanism seed claim" is
   operationalized as "layer-0 fact/mechanism node" — add a one-line clarification to
   docs/04 §Evidence Seeding step 4 (or docs/09 V-SWEEP-01) in the SAME commit. Docs:
   docs/04 §Evidence Seeding, docs/05 pipeline, docs/09 V-SWEEP.

3. T-r3-7  validate-from-claimed. validate/proof.py:43 rejects non-"validating"; change so
   claimed|running performs `complete` first (emit the complete event via queue engine, then
   proceed) — two events, one command. Same for validate docs-result (docsdb path). Manifest/
   lease scan (V-PATH-04) must still run against the claim-time lease.manifest. Docs: docs/05
   §Validation Gate (r3), docs/10 §4 rows validate result/docs-result, V-Q-01 table docs/05.

4. T-r3-9  ui serve --auto-rebuild. Thread the flag from cli app → ui/app.py factory; when a
   poll (e.g. /api/overview) finds stale_index true AND flag on, run db rebuild then serve
   fresh; flag OFF → banner behavior byte-identical. Docs: docs/07 §WebUI (`ui serve`),
   docs/10 §4 `ui serve` row, docs/12 P3/stale banner.

5. T-r3-10 drift test. Assert prompts/proof_worker.txt contains "SELF-CHECK"; docs_worker.txt
   contains the coverage numbers (2–5 docs / 4–10 EUs, en-dash) + "DISCONFIRMING". Add to
   tests/contract/test_polish_guards.py (or new test_template_drift.py). Templates already
   shipped in r3-core — this is the drift guard only.

Doc-sync discipline (CLAUDE.md): any deviation ships the doc edit in the same commit; flag
each doc edit in log.md. Do NOT add CLI/schema surface beyond docs/10 §4 / docs/08 (escalate).

## STAGED AFTER m5: search program S1-S5 (docs/13-18, design-frozen) — the v1.1 milestone;
adopt via a docs/00 changelog entry + a docs/11 worklist, per docs/13 §Normativity. NOT this stage.

## ai-jobs run data (regression reference): data/projects/ai-jobs (24 EU, 12 docs, 10
verdicts, 122 events — the V-PATH-04 failures were QE-000048/51/64/101/104).

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
