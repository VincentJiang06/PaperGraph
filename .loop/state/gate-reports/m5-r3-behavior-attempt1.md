# Gate report — m5-r3-behavior — attempt 1

**Result: PASS.** Full suite green.

```
399 passed, 1 warning in ~11s
```

Baseline at re-entry: 386 green. Delta: +13 tests (all new, additive — no prior
test deleted or weakened). Gate side-conditions: `V-SWEEP-01 ∈ registry` ✓ ;
`tests/contract/test_v_sweep.py` present ✓ ; default `pytest -q` green ✓.

Gate command: `.venv/bin/python -m pytest -q` (from project root).

---

## Per-item (A28–A32)

### A28 — T-r3-4 evidence floor ≥2 EU from ≥2 distinct documents (ONE shared helper, 3 sites)
- Shared helper (single source of truth): `src/paperproof/graph/model.py:170-207`
  — `evidence_doc_map(paths)` (evidence_id→doc_id from `docs/evidence_units.jsonl`),
  `evidence_binding_counts(node, eu_doc)` → `(binding_count, distinct_doc_count)`,
  `meets_evidence_floor(node, eu_doc)` = `binding_count>=2 AND distinct_docs>=2`.
- Site 1 — MSA-4: `src/paperproof/graph/commands.py:114-121` (was `>=1`).
- Site 2 — V-FRZ-02: `src/paperproof/freeze/apply.py:128-135` (was `<1`).
- Site 3 — compiler `missing_evidence` gap: `src/paperproof/compiler/dry_run.py:50-56`.
- Consistency bonus: the WebUI MSA-4 mirror (`src/paperproof/ui/readmodel.py:185-190`)
  now uses the same `meets_evidence_floor` helper (fed from the indexed EUs) so it
  can never diverge from the CLI/freeze path.
- S7 fixtures LIFTED: `tests/fakes/scenario.py::boe_docs_result_spec` now yields 2
  documents (BoE + IMF) → 2 EvidenceUnits from 2 distinct docs (each quote verbatim,
  V-DR-05); `s7_script` mechanism M binds `["EU-001","EU-002"]`. S7 stays green with a
  zero-gap dry run by construction.
- Negative tests added: `tests/contract/test_v_frz.py` — a 1-binding spine mechanism
  AND a 2-EU-same-document spine mechanism each FAIL `graph msa-check` (MSA-4) AND
  `freeze apply --level spine` (V-FRZ-02); plus a positive 2-EU/2-doc MSA-4 pass.

### A29 — T-r3-5 V-SWEEP-01 sweep floor gate (NEW rule)
- Rule module: `src/paperproof/validate/rules/v_sweep.py` — `check_sweep_floor` /
  `node_meets_floor` / `coverage`. REUSES `docsdb/pack.py::_requested_eus` for the
  request→DRES→ingested_from trace (imported locally to avoid a load-time cycle).
- Registered: `src/paperproof/validate/registry.py:37` (`V-SWEEP-01`), module wired
  into imports/`__all__`.
- Enforced: `src/paperproof/expander/ingest.py` — `_check_sweep_gate` runs after
  V-EXP, before commit, and fires only on the FIRST proposal with `layer>=1` (no
  layer≥1 node exists yet). Floor per layer-0 fact/mechanism node: (≥2 EU from ≥2
  distinct docs requested-for-it) OR (≥2 not_found DocsRequests targeting it).
- Informational line: `graph msa-check` now returns `sweep_coverage`
  (`src/paperproof/graph/commands.py:156-160`) — NOT a pass/fail MSA item; MSA-1..9
  unchanged/un-renumbered.
- Coverage: `SCENARIO_COVERED["V-SWEEP-01"]` added
  (`tests/contract/test_rule_coverage.py`); new `tests/contract/test_v_sweep.py`
  (refuse-below-floor / pass-after-2EU-2docs / same-doc-still-refused /
  pass-after-2-not-found / vacuous-when-no-fact-mechanism-seed).

### A30 — T-r3-7 validate-from-claimed (implicit complete)
- Proof path: `src/paperproof/validate/proof.py:40-53` — an item in `claimed`/`running`
  is `complete`d here (emits the complete event) then validated; `validating` behaves
  as before; other states still error. The V-PATH-04 lease scan still runs against the
  claim-time `lease.manifest` (which `queue.complete` preserves).
- Docs path: `src/paperproof/docsdb/ingest.py:167-178` (`ingest_result`) — same
  implicit-complete. This is the docs analog that emits `validate_pass`+`commit`; the
  standalone `validate docs-result` CLI is a pure V-PATH+V-DR check (no state change,
  already accepts a claimed item), so the state-advancing implicit-complete belongs in
  `ingest_result`. (Interpretation flagged below.)
- Tests: `tests/contract/test_v_q.py` — proof `validate result` from claimed emits
  `[enqueue, claim, complete, validate_pass]` and `verify` exits 0; `docs ingest-result`
  from claimed emits `[enqueue, claim, complete, validate_pass, commit]`. `v_q.verify_queue`
  clean (no illegal V-Q-01).

### A31 — T-r3-9 `ui serve --auto-rebuild`
- Flag threaded: CLI `ui serve --auto-rebuild` (`src/paperproof/cli/app.py:294-306`) →
  `ui.app.serve(paths, port, auto_rebuild)` → `create_app(root, project, auto_rebuild)`
  → `_ensure_index(paths, auto_rebuild)` (`src/paperproof/ui/app.py:28-58`): when ON and
  a poll finds the index stale, it rebuilds; when OFF (default), a stale index is left
  as-is (banner behavior byte-for-byte unchanged).
- Test: `tests/integration/test_api.py::test_auto_rebuild_clears_stale_on_poll` — with
  the flag a touched JSONL is reconciled on the next poll (stale clears, fresh data);
  without it stale stays true and the indexed value is still served. The pre-existing
  OFF-path test (`test_stale_flips_and_endpoint_reads_index_not_jsonl`) uses the default
  factory and is unchanged/green.

### A32 — T-r3-10 template drift test
- New `tests/contract/test_template_drift.py`: asserts `prompts/proof_worker.txt`
  contains `SELF-CHECK`; `prompts/docs_worker.txt` contains
  `target 2-5 documents and 4-10 evidence units` and `DISCONFIRMING`.

---

## Doc/ files amended (doc-sync, CLAUDE.md)
1. `docs/04-docs-database.md` (§Evidence Seeding step 4) — added the required
   operationalization note: a "fact/mechanism seed claim" is enforced as a LAYER-0
   fact/mechanism node; REQUESTED-for-N traced request→DRES→ingested_from. (T-r3-5)
2. `docs/09-verification.md` (V-SWEEP-01) — same operationalization clarification.
3. `docs/10-v1-design.md` (§4 `docs ingest-result` row) — noted it accepts
   claimed/running and completes implicitly (r3), consistent with the docs/05
   Validation Gate change. (T-r3-7)

## Pre-existing tests modified (none weakened)
- `tests/fakes/scenario.py` — LIFTED S7 evidence fixtures (2 docs / 2 EUs; M binds
  both) to satisfy the r3 floor. This is the T-r3-4-mandated fixture lift, not an
  assertion weakening. All S7/monitor/api consumers stay green.
- `tests/contract/test_v_frz.py`, `tests/contract/test_v_q.py`,
  `tests/integration/test_api.py`, `tests/contract/test_rule_coverage.py` — ADDED
  tests/entries only (no existing assertion changed).

## Escalations / interpretation notes (no blockers)
- **T-r3-10 dash discrepancy (resolved by matching shipped bytes).** The task/contract
  wrote the coverage numbers with EN-DASH ("2–5"/"4–10", "note EN-DASH, matches the
  shipped text"), but the SHIPPED `prompts/docs_worker.txt` (frozen in r3-core) uses
  HYPHEN-MINUS ("2-5"/"4-10"). A drift guard must match the shipped file, so the test
  asserts the hyphen form. No prompt bytes were changed.
- **T-r3-7 "validate docs-result" target.** Contract A30 lists `validate docs-result`
  with "two events — complete + validate_pass/fail". In code the state-advancing docs
  validation is `docs ingest-result` (`ingest_result`), which emits validate_pass; the
  CLI `validate docs-result` is a pure dry check that changes no state (and already
  accepts a claimed item). Implicit-complete was therefore implemented in
  `ingest_result` (the docs validate-and-advance path). No CLI/schema surface added.
- No new CLI command or schema field was introduced. `--auto-rebuild` is an OPTION on
  the existing `ui serve` command (already in docs/10 §4 / the closed CLI list); the
  CLI-conformance meta-test stays green.

---

## Evaluator verdict

**Result: PASS** (fresh adversarial evaluator; nothing trusted from the Generator's
self-report — every claim below was independently re-derived and re-run).

**Independently-verified suite:** `399 passed, 1 warning in 12.30s` in a clean shell
(`.venv/bin/python -m pytest -q`). All-dots progress line — **0 skipped, 0 xfailed,
0 deselected-to-dodge**. Baseline was 386 @ HEAD 6072f39; delta +13 is purely
additive (diffed every changed test — see below). `V-SWEEP-01 ∈ registry` ✓ ;
`tests/contract/test_v_sweep.py` present ✓.

### What I independently PROVED (own fixtures, not the shipped ones)

- **A28 floor consistency — PASS.** grep proved exactly ONE floor fn
  (`graph/model.py:203 meets_evidence_floor`); no leftover independent binding
  comparison survives anywhere in `src/` (grep for `len(evidence_bindings)`/`>=1`/`<1`
  near evidence = empty). All THREE sites call it — MSA-4 (`graph/commands.py:117`),
  V-FRZ-02 (`freeze/apply.py:133`), compiler `missing_evidence`
  (`compiler/dry_run.py:54`) — plus the UI mirror (`ui/readmodel.py:187`, same helper,
  fed from the derived index). My own `fact`-node repro (Generator's tests used
  `mechanism`): `["EU-001"]` → **all 3 reject**; 2 EU/**same** doc → **all 3 reject**;
  2 EU / 2 distinct docs → **all 3 pass**. Distinct-document requirement is real.
- **A29 sweep scope — PASS.** `expand ingest` sweep gate fires ONLY on the first
  `layer>=1` proposal: with a pre-existing `layer>=1` node it does NOT fire (even with an
  unmet seed floor); a `layer==0` proposal is never gated; the first `layer>=1` with an
  unmet floor fires `V-SWEEP-01`. `graph msa-check` returns **exactly 9** MSA items
  (MSA-1..9) with `sweep_coverage` as a SEPARATE informational key — not a 10th gate.
  `_requested_eus` (request→DRES→ingested_from) backs "requested-for-N"; a not_found pass
  needs ≥2 not_found angles (confirmed in `v_sweep.node_meets_floor`).
- **A30 implicit-complete — PASS (with a doc-sync finding, below).** proof `validate
  result` from a fresh `claimed` item (no explicit `queue complete`) emits exactly
  `[enqueue, claim, complete, validate_pass]`, lands `validated`, `verify` exit 0,
  `v_q.verify_queue == []`. `complete` = claimed→validating and `validate_pass` =
  validating→validated are both legal per docs/05:94-95 → no illegal V-Q-01.
- **A31 auto-rebuild — PASS.** OFF path is byte-unchanged by construction (the new
  rebuild branch in `_ensure_index` is guarded by `auto_rebuild`, default False); ON
  clears stale on the next poll. `--auto-rebuild` is an OPTION on the existing `ui serve`
  — no new command, no schema model touched (no `schemas/` file in the diff); CLI
  conformance stays green.
- **A32 drift test — NOT hollow.** The asserted bytes
  `target 2-5 documents and 4-10 evidence units` are the *exact* shipped
  `prompts/docs_worker.txt:23` (hyphen-minus, not the contract's en-dash). Removing the
  block makes `in text` False → the test fails. The hyphen-vs-en-dash resolution is
  correct: a drift guard must pin the shipped file. `proof_worker.txt:40` carries
  `SELF-CHECK`.

### Weakened-test / reward-hack audit — CLEAN

- `tests/fakes/scenario.py` S7 lift is an **evidence-SUPPLY** change (BoE-only →
  BoE+IMF, 2 EU / 2 distinct docs; M binds `["EU-001","EU-002"]`), NOT an assertion
  relaxation. `tests/integration/test_s7_full_pipeline.py` is **untouched** and still
  asserts `all_pass` (l.74), **zero-gap** dry run `gaps == []` (l.91), `audit passed`
  (l.130), and **trace resolves every spine node** (l.133-146). The lift is load-bearing:
  the mechanism M is a spine node, so under the new compiler floor a 1-EU M would have
  produced a `missing_evidence` gap — zero-gap only holds because M genuinely meets the
  floor. IMF EU quote is verbatim in its doc text (V-DR-05 holds).
- Every other changed test (`test_v_frz`, `test_v_q`, `test_api`, `test_rule_coverage`)
  is ADD-only; no pre-existing assertion was deleted, loosened, or made vacuous.
- The three doc edits (docs/04, docs/09, docs/10) each correctly describe shipped code
  and none widens the CLI/schema surface or legalizes a bug.

### T-r3-7 docs-path question — my adjudication

**It satisfies the r3 ergonomic intent for the docs loop; it is NOT a spec-drift dodge,
BUT it ships with a doc-sync defect the Orchestrator must fix.**

- Intent satisfied: `docs ingest-result` — the command the docs Layer Loop actually uses
  to advance items (docs/05:251) — now accepts a `claimed`/`running` item and does
  complete + validate_pass + commit in one call (proven by the shipped test + code at
  `docsdb/ingest.py:170`). One command from claimed for the docs loop: delivered.
- Not "broken": I ran `validate docs-result` against a `claimed` item — it performs NO
  state transition (ops stayed `[enqueue, claim]`, status stayed `claimed`). That is BY
  DESIGN — `validate docs-result` is a pure V-PATH+V-DR dry check (docs/10 §4;
  `docsdb/commands.py:91`); putting implicit-complete there would contradict its
  no-state-change contract. The Generator's engineering choice is correct.
- **FINDING F1 (doc-sync, non-blocking, Orchestrator must fix before/at tag).**
  docs/05 §Validation Gate **lines 200-202** ("`validate result|docs-result` … performs
  the `complete` transition itself") and the Status Machine **lines 94-95** ("performed
  implicitly by `validate`" / validate-pass = "`validate … docs-result`") still literally
  attribute docs implicit-complete to `validate docs-result`. In shipped code that
  behavior lives in `docs ingest-result`. The Generator amended docs/10 §4's
  ingest-result row but did NOT reconcile docs/05. Per CLAUDE.md doc-first / A27 this
  reconciliation should ship in the same change. Fix: in docs/05:200-202 and 94-95, name
  `docs ingest-result` as the docs-side implicit-complete path and note that
  `validate docs-result` stays a stateless dry check. No code change required.

### Bottom line

All five behaviors (A28–A32) are functionally delivered and independently verified;
the suite is honestly green (no skips/xfails, no weakened assertions, no reward-hack);
the S7 lift is a genuine supply change. The sole defect is F1 (a documentation-wording
inconsistency in docs/05 that mis-attributes the docs implicit-complete). It breaks no
behavior, hides no bug, and is not reward-hacking, so it does not block the gate — but
the Orchestrator MUST land the docs/05 reconciliation (F1) as part of this stage's
doc-first discipline before tagging `gate/m5-r3-behavior`.
