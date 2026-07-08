# Contract — PaperGraph v1 build

The negotiated, graded criteria (from `papergraph-v1-build.loop.json`). The loop
grades THIS, not the raw spec. Each assertion is machine-gradable unless marked
`human-verify:`. `[ ]` open · `[x]` proven at a gate.

## Environment (established at loop start, 2026-07-07)
- System python is 3.9.6; spec requires 3.12+. Use the uv-managed venv:
  `.venv/` (CPython 3.12.13). Gate commands run via `.venv/bin/python -m pytest`.
- Install: `uv pip install -e ".[dev]"` (into `.venv`).
- final-audit fresh-clone gate must pin 3.12 (`uv venv --python 3.12`), NOT the
  bare `python3 -m venv` in the original design (which would grab 3.9). Adjust
  that gate command when reaching final-audit; recorded here so it isn't lost.

## Assertions

- [x] A1  package installs editable w/ dev extras on py>=3.12 · `uv pip install -e ".[dev]"` · m0 ✓gate/m0
- [x] A2  every schema_version round-trips; rejects unknown fields + out-of-enum · test_schemas · m0 ✓ (23 schemas)
- [x] A3  spec build on P4 → byte-exact golden PaperSpec+Contract under PAPERPROOF_NOW · test_v_spec -k golden · m0 ✓ (evaluator re-derived by hand)
- [x] A4  each V-SPEC rule has a failing topic fixture rejected w/ that rule id · test_v_spec · m0 ✓
- [x] A5  JSONL store append-only, latest-by-id, rejects path traversal · test_jsonl_store · m0 ✓ (evaluator attacked symlink/traversal)
- [x] A6  typer app = exactly docs/10 §4 closed list (stubs=envelope+NOT-IMPLEMENTED+exit1); one envelope always · test_cli_envelope · m0 ✓ (43 cmds both directions)
- [x] A7  textutil = docs/09 §0 exactly (CJK tok/sentence, frozen 82-word stoplist) · test_textutil · m0 ✓
- [x] A8  24 golden decision rows compute documented verdicts · test_decision_table -k golden · m1
- [x] A9  totality fuzz: every enum combo → one verdict or V-PR-14/15/05 reject · test_decision_table -k totality · m1
- [x] A10 hostile H01–H18 rejected w/ named rule in failed_rules · test_v_pr · m1
- [x] A11 S1 bridge wiring (C,D + C→B,D→B; re-proof blocked_by 4; pass(conditional); C,D in spine) · test_s1 · m1
- [x] A12 S4 8 items/4 workers all committed, no double leases, replayable log · test_s4 · m1
- [x] A13 S5 expiry attempt+1 then dead>3; S6 stale→-r2, old bundles immutable · test_s5,test_s6 · m1
- [x] A14 two identical S1 runs → byte-identical canonical files · test_determinism · m1
- [x] A15 every rule id has pass+fail fixtures OR SCENARIO_COVERED; meta-test fails on gaps both ways · test_rule_coverage · cross-cutting
- [x] A16 docs D01–D05 rejected w/ named rules; quote_match accepts true/rejects fake · test_v_dr · m2
- [x] A17 S2 identical 2nd request=cache no work item; 3rd needs_docs → born-dead item · test_s2 · m2
- [x] A18 S3 cascade tombstones incident edges endpoint_rejected + cancels items; verify=0 · test_s3 · m2
- [x] A19 each V-FRZ precondition violation refused; unfreeze re-opens via batch commit · test_v_frz · m3
- [x] A20 S7 P4→audited prose: MSA-1..9 asserted, zero-gap dry run, DraftMap determinism, audit passed, trace resolves every spine node · test_s7 · m3
- [x] A21 annotation grammar + audit finding kinds per docs/06; seeded violations caught, clean passes · test_v_prose_aud · m3
- [x] A22 S8 db rebuild idempotent (same manifest hash); corrupt JSONL → every CLI exit 3 file+line · test_s8 · m4
- [x] A23 /api answers six Overview questions from S7 fixture; stale_index truthful · test_api · m4
- [x] A24 default pytest excludes live markers · `grep "not live" pyproject.toml` · cross-cutting ✓ (verified at m0)
- [x] A25 suite passes from fresh clone in clean venv · fresh-clone gate · final-audit
- [ ] A26 human-verify: live smoke (real workers) run by human, recorded in agent_notes/milestones/ · cross-cutting
- [ ] A27 human-verify: doc-first — any src deviation from docs/ ships doc amendment same commit · cross-cutting

## Stage m5-r3-behavior (r3 behavior upgrades — the 5 items r3-core deferred; gated by docs/11 §10 T-r3-4/5/7/9/10)

- [x] A28 (T-r3-4) evidence floor ≥2 EU from ≥2 distinct documents — ONE floor fn (graph/model.py:203)
        called by MSA-4 (graph/commands.py:117), V-FRZ-02 (freeze/apply.py:133), compiler
        missing_evidence (dry_run.py:54) + UI mirror (readmodel.py:187); evaluator proved 1-binding
        AND 2-EU-same-doc each fail msa-check AND spine freeze; 2-EU/2-doc passes; S7 lifted
        (BoE+IMF), still zero-gap + audit + trace · test_v_frz + test_s7 · m5 ✓
- [x] A29 (T-r3-5) V-SWEEP-01 registered + SCENARIO_COVERED; expand ingest refuses first layer>=1
        proposal while a fact/mechanism layer-0 node lacks the floor, passes once met; fires ONLY on
        first beyond-layer-0; msa-check still exactly 9 items + informational sweep_coverage · test_v_sweep · m5 ✓
- [x] A30 (T-r3-7) implicit complete from claimed/running: validate result (proof) emits
        [complete, validate_pass] one command; docs ingest-result (docs loop) same; validate docs-result
        stays a stateless dry check by design; verify exit 0, no illegal V-Q-01 · test_v_q · m5 ✓
        (F1 doc-sync: docs/05 §Validation Gate + complete row reconciled to name the real paths)
- [x] A31 (T-r3-9) ui serve --auto-rebuild rebuilds a stale index on poll; OFF path byte-unchanged
        (flag-guarded branch); option on existing ui serve, no new command/schema · test_api · m5 ✓
- [x] A32 (T-r3-10) drift test asserts shipped bytes (proof SELF-CHECK; docs "2-5 documents"/"4-10
        evidence units" hyphen + DISCONFIRMING); removing the block fails the test · test_template_drift · m5 ✓

Gate (m5): PASS — 399 green (386 baseline +13), independently re-run by a fresh adversarial
Evaluator; all 5 probes reproduced with its own fixtures; weakened-test audit clean. F1
(docs/05 stale on the docs implicit-complete path) reconciled by the Orchestrator before tagging.

## Stage m6b-s3-lite (S3 source registry — Stage A-lite; docs/16, docs/00 adoption)

Registry + recipes + provenance only. Stage B triangulation (V-SRC-04) NOT built.

- [x] A37 schemas: source_profile.v1 (adds tier_note) + document.v2 (=v1+provenance)
        registered + golden fixtures round-trip; document.v1 stays registered and
        READABLE (parses + validates as v1); extra=forbid on all. · test_schemas +
        test_v_src::test_document_v2_roundtrip_and_v1_still_valid · m6b
- [x] A38 ingestor LEARNS + provenance: every web-domain ingest upserts (appends) a
        SourceProfile — tier via the fixed source_type→tier table (docs/16),
        blocked_direct read defensively from search_log OR query_log outcome=blocked
        (S1 integration point), fetch method from provenance; ingested docs are
        document.v2 with provenance (tier denormalized via registry, fetch_method
        direct on the v1 path, quoted_via for secondary_quote); dispatch excerpt =
        every T1 + every facet-matched profile [V-SRC-05]; docs_worker prompt gains a
        read-only REGISTRY block. · test_v_src (T-S3-1/4) + test_template_drift · m6b
- [x] A39 rules + CLI + storage + tests: V-SRC-01/02/03/05 in v_src.py, registered +
        rule-coverage green; `docs source list|set` (subgroup of docs; set=append,
        silent tier-lowering refused by V-SRC-03); storage docs/sources.jsonl (init +
        verify sweep); T-S3-1/2/4 green and all prior 399 green (T-S3-back). ·
        test_v_src + test_rule_coverage + test_cli_envelope + verify · m6b
