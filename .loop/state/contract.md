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
GATE PASSED, tagged gate/m5-r3-behavior, pushed to GitHub.

## Stage m6-s1-search-planning (Search Program S1, adopted 2026-07-08; docs/14, worklist docs/11 §12)

First set of the search program's Stage A (v1.1). Makes evidence search ACCOUNTABLE:
code compiles a deterministic SearchPlan; the worker accounts for every planned query.
Baseline: 399 green @ gate/m5-r3-behavior. Blast radius includes the core docs schema
(docs_result v1→v2) — back-compat is a graded assertion.

- [x] A33 (T-S1-1) plan compiler deterministic & doc-faithful — byte-exact golden incl. CJK; core ≤6
        cap/tie=firstocc/minus-scope; counter in EVERY plan (survives max_queries cap). Evaluator re-proved
        with own inputs · test_search_plan · m6 ✓
- [x] A34 (T-S1-2) V-SP-01..05 registered + ENFORCED (each fail_ fixture → that rule id; wired into
        validate docs-result AND docs ingest-result, v2-only); docs_result.v2 round-trips, v1 valid v1 ·
        test_v_sp (17) · m6 ✓
- [x] A35 (T-S1-3) hostile docs_taken>urls_seen → ['V-SP-03']; `docs plan --request` byte-identical reprint ·
        test_v_sp · m6 ✓
- [x] A36 (T-S1-back) 437 green, no weakened prior assertion (evaluator diff vs gate/m5); plan attached at
        BOTH dispatch sites (commands.py:85, committer _wire_docs apply.py:539); V-DR-06 works v1+v2 · full suite · m6 ✓
        PROVENANCE: S1 impl authored by an INTERRUPTED m6-s1 generator, swept into 967a8cf ("no code yet" msg
        inaccurate); worktree agent added the missing test_v_sp.py; fresh Evaluator gated the whole thing.
        F1 (evaluator FAIL→fix): docs/09 got the ### V-SP block + V-DR-06 v2 re-expression (were promised, undone).

Gate (m6): `.venv/bin/python -m pytest -q` green AND V-SP-01..05 ∈ registry AND
tests/contract/test_v_sp.py present AND no weakened pre-S1 docs assertion. Doc-sync:
any deviation ships the doc amendment same change. On PASS → tag gate/m6-s1-search-planning, push GitHub.

## Stage m6b-s3-lite-source-registry (Search Program S3-lite, adopted 2026-07-08; docs/16, worklist docs/11 §12)

Runs in PARALLEL with m6-s1 (worktree-isolated). Source tiers + fetch recipes + provenance;
durable memory of where evidence lives and how to fetch it. Baseline 399 @ gate/m5-r3-behavior.
Coupling: `blocked_direct` learning reads S1's query_log — code it defensively; reconcile at merge.
Triangulation (V-SRC-04) is Stage B — NOT in this stage.

- [x] A37 (T-S3-1/2) ingest LEARNS a SourceProfile per domain: blocked_direct + workaround from a
        blocked query_log entry; tier via the fixed source_type→tier table (golden); updates are
        appends (latest-per-domain), silent tier-lowering rejected (V-SRC-03) · test_v_src · m6b
- [x] A38 (T-S3-4) provenance on every ingested doc (retrieved_at, fetch_method∈enum, tier∈enum)
        [V-SRC-01]; secondary_quote names an existing quoted_via carrier, dangling ⇒ V-SRC-02;
        dispatch registry excerpt = all T1 + facet-domain matches [V-SRC-05]; document.v2 round-trips,
        v1 still validates v1 · test_v_src + rule_coverage · m6b
- [x] A39 (T-S3-back) NO REGRESSION (399 + S1): document.v2 + `docs source list|set` CLI + registry
        prompt block added without weakening any ingest/V-DR/cascade assertion; V-SRC-04 NOT built;
        msa/freeze floors unchanged from m5 · full suite + evaluator diff · m6b

Gate (m6b): pytest green AND V-SRC-01/02/03/05 ∈ registry AND test_v_src.py present AND no weakened
assertion. On PASS → tag gate/m6b-s3-lite-source-registry, push GitHub.

## Stage m7-s2-search-orchestra (Search Program S2, adopted 2026-07-08; docs/15, worklist docs/11 §12)

Wave 2 of Stage A (needs S1). Turns a DocsRequest into a WAVE: parallel per-angle
members (each executing its S1 plan), a DETERMINISTIC merger (code, no LLM), a
fresh adversarial coverage critic (bounded worker, closed form) — CODE computes
the verdict over ≤2 rounds. NOTE: this worktree branched from an S1-only base
(437 green), NOT the parent's assumed S1+S3-lite 457 — S3-lite (test_v_src.py)
is absent here; the merge onto main must re-verify the shared-file hunks land
alongside whatever S3 state main carries.

- [x] A40 (T-S2-1) merger goldens: dup content_hash + tracking-param URL variant +
        dup EU collapse to a deterministic merged docs_result.v2 (byte-identical on
        re-merge); every merged doc/EU traces to a member (V-WAVE-02); canonical_url
        strips {utm_*,gclid,fbclid,ref}+default port+fragment, collapses //, strips one
        trailing / · test_s2_wave (contract) · m7
- [x] A41 (T-S2-2) wave-verdict table: sufficient|followup|closed over every
        angle_covered combo × primary × disconfirming × round; R_MAX=2 never followup
        (no infinite loop); followup opens one member per no_attempt angle + per
        expected_source (suggested_query→hint). CODE computes it, never the critic ·
        test_s2_wave (contract) · m7
- [x] A42 (T-S2-3) hostile critic smuggling documents/evidence_units ⇒ V-WAVE-03;
        closed-enum-incomplete form + >3 expected_sources ⇒ V-WAVE-03; V-WAVE-01/04/05
        pass+fail; FakeCriticWorker added · test_s2_wave (contract) + test_rule_coverage · m7
- [x] A43 (T-S2-4) `docs wave --fan` fans all angles (distinct outputs; single item
        superseded); a never-covered angle CLOSES at R_MAX recording it (no infinite
        loop) + exactly one DRES per wave [V-WAVE-05]; all-covered ⇒ sufficient round 1;
        non-fan ⇒ single member unchanged; verify exit 0 · test_s2_wave (integration) · m7
- [x] A43-back  467 green (437 baseline + 30); no weakened pre-S2 assertion
        (test_s2_docs_loop untouched; test_cli_envelope + test_rule_coverage only
        ADDED entries); docs 15/09/10/11 amended same change · full suite · m7

Gate (m7): `.venv/bin/python -m pytest -q` green AND V-WAVE-01..05 ∈ registry AND
tests/{contract,integration}/test_s2_wave.py present AND FakeCriticWorker in
tests/fakes/workers.py AND no weakened pre-S2 assertion. Doc-sync: any deviation
ships the doc amendment same change. On PASS → tag gate/m7-s2-search-orchestra.

## PARALLEL BUILD STRATEGY (Stage A / v1.1)
Wave 1 (parallel worktrees, NOW): m6-s1 + m6b-s3-lite. Integrate S1 first, then S3 (merge the ~4
shared files: registry.py, schema registry, prompts/docs_worker.txt, docsdb ingest); gate + fresh
Evaluator per set. Wave 2: m7-s2 (needs S1). Then Stage A done → user fork on S4(v1.2)/S5(v2).
STATUS: S1 gated+pushed (gate/m6-s1). S3 merged (457 green @ ed04781), evaluator running. S2 launched.

## Stage m7-s2-search-orchestra (Search Program S2, adopted 2026-07-08; docs/15, worklist docs/11 §12)

Completes Stage A. Waves (parallel per-angle members) + deterministic merger + fresh adversarial
coverage critic -> code computes the wave verdict (<=2 rounds). Baseline 457 @ ed04781 (S1+S3).
Built in a worktree from the S2-adoption commit; needs S1 (members execute S1 plans), coexists with S3.

- [ ] A40 (T-S2-1) merger determinism: same terminal member set => BYTE-identical merged docs_result.v2;
        dedup by content_hash then canonical URL (frozen tracking-param strip); dup EUs dropped; every
        merged doc/EU traces to exactly one member (V-WAVE-02) · test_v_wave · m7
- [ ] A41 (T-S2-2) CODE computes the wave verdict (sufficient|followup|closed) from the critic's CLOSED
        form over every angle_covered combo; R_MAX=2; followup opens one member per no_attempt angle +
        per expected_source; member outputs pairwise-distinct (V-WAVE-01/04) · test_v_wave · m7
- [ ] A42 (T-S2-3/4) hostile critic smuggling documents/evidence_units rejected (V-WAVE-03); only the
        merged result ingested, one DRES per wave (V-WAVE-05); `docs wave --request [--fan]` fans members ·
        test_v_wave + cli · m7
- [ ] A43 (T-S2-back) NO REGRESSION (457 + S2 green): waves coexist with S1 plans + S3 registry; a non-fan
        reactive request still runs as a single member unchanged · full suite + evaluator diff · m7

Gate (m7): pytest green AND V-WAVE-01..05 in registry AND test_v_wave.py present AND no weakened assertion.
On PASS -> tag gate/m7-s2-search-orchestra, push GitHub. Then Stage A COMPLETE -> raise S4/S5 fork to user.
