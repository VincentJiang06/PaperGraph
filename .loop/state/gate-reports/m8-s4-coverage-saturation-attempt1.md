# Gate report — m8-s4-coverage-saturation (attempt 1)

Status: **PASS** (worktree build). Full suite `.venv/bin/python -m pytest -q`:
**508 passed** (baseline at branch point: 487). `paperproof verify` exits 0 on a
coverage/wave-built S7 project (verified end-to-end via the CLI + inside the S7
integration test's spine freeze / V-FRZ-04).

Worktree branch: `worktree-agent-adba6a64c9007b8cb` (branched from `c070611`).

## Supersession verified (the central risk)
- `grep -rn "meets_evidence_floor\|>= 2" src/paperproof/graph src/paperproof/freeze` → **none**.
- No docs verdict-count cap in the committer (removed `_needs_docs_verdicts`,
  `_new_target_evidence_since`, and the `len(verdicts) >= 3` dead-letter). The
  BRIDGE round cap (`_bridge_rounds`, `rounds >= 2`) is a separate cap and stays.
- `meets_evidence_floor` no longer exists anywhere in src/ or tests/.

## Per-assertion (A44–A47)
- **A44 (V-COV-01, ledger fold)** — DERIVED per-node coverage ledger, a
  deterministic fold; `docsdb/coverage.py:target_ledger` / `build_ledger`.
  Determinism golden + field goldens: `tests/contract/test_v_cov.py:138`
  (`test_ledger_fold_determinism`). `docs coverage [--node]`:
  `docsdb/commands.py:coverage` + `cli/app.py` (`docs_coverage`); `/api/coverage`:
  `ui/readmodel.py:coverage` + `ui/app.py`. Saturation truth table
  `test_v_cov.py:test_saturation_truth_table`.
- **A45 (V-COV-03, saturation replaces the cap)** — committer
  `committer/apply.py:_plan_needs_docs` now consults `coverage.target_ledger`:
  not-saturated ⇒ always open search; saturated + floor-unmet ⇒ `dead_letter`
  reason=`saturated`; saturated + floor-met ⇒ `human_review` (no born-dead).
  Regressions: `test_v_cov.py::test_saturation_fresh_target_not_dead_lettered`
  (a) and `::test_saturation_floor_unmet_born_dead` (b). Migrated cap tests:
  `test_r3_core.py::test_orchestrator_requests_do_not_saturate_a_healthy_target`
  and `test_s2_docs_loop.py` phase 5 (both now assert NOT-born-dead pre-saturation).
- **A46 (V-COV-04, role-profile floors)** — one function
  `coverage._role_floor_met` behind `coverage.meets_floor`; MSA-4
  (`graph/commands.py`), V-FRZ-02 (`freeze/apply.py`), compiler missing_evidence
  (`compiler/dry_run.py`) all delegate to it. `msa-check` prints the per-node
  ledger line (`coverage.floor_line`) for every miss. ContextPack coverage block
  [V-COV-02]: `schemas/proof.py` (`ContextPack.coverage`) + `prooftask/builder.py`.
  V-COV-05 narrow-inheritance: `validate/rules/v_cov.py:rounds_reset_on_narrow` +
  natural node_id inheritance; `test_v_cov.py::test_narrow_inherits_ledger`.
  Floor tests: `test_v_cov.py` (nonspine/bridge/msa4-line) + migrated `test_v_frz.py`.
- **A47 (V-SRC-04 triangulation + no regression)** — `coverage.triangulated` +
  `validate/rules/v_src.py:check_triangulation`; enforced at freeze
  (`freeze/apply.py` appends V-SRC-04 when a spine profile is non-triangulated),
  reported by msa-check via the floor line. Tests: `test_v_cov.py::test_triangulation_*`
  (same-publisher T3 pair fails; T1+T4 passes; T5-only fails; enforced at freeze).
  Full prior suite green; S7's spine mechanism M already satisfies the role floor
  incl. triangulation (BoE T1 + IMF T1 distinct docs) + counter-attempt (its
  completed search), so no S7 fixture change was needed.

## Old rules REMOVED (file:line at edit time)
- `graph/model.py` — deleted `meets_evidence_floor` (`binding_count >= 2 and
  distinct_docs >= 2`) and `evidence_binding_counts`.
- `committer/apply.py` — deleted `_needs_docs_verdicts`, `_new_target_evidence_since`,
  and the `_plan_needs_docs` docs cap (`len(verdicts) >= 3` → `dead_letter "docs cap reached"`).

## Docs amended (doc-sync)
- `docs/09` — **added the `### V-COV` block (V-COV-01..05)**; rewrote V-FRZ-02 to
  delegate to the role-profile floor; flipped V-SRC-04 from "NOT ADOPTED" to the
  full adopted triangulation rule line.
- `docs/16` — flipped the triangulation section + V-SRC-04 + adoption note + test
  note (T-S3-3) from "NOT ADOPTED/not built" to ADOPTED/BINDING.

## Pre-existing tests migrated (not weakened — stricter)
- `test_v_frz.py` — floor cases now require triangulation; added a
  `two_docs_not_triangulated` (same-pub T3) FAIL case (+V-SRC-04) and a
  `role_profile_needs_counter_angle` FAIL case; positive test now seeds T1+T4 +
  a completed search. STRICTER.
- `test_v_cdr.py::test_gap_missing_evidence` — note text updated to the role-profile
  floor; the zero-binding spine mechanism still fails (STRICTER-compatible).
- `test_r3_core.py` test 3 — migrated off the removed cap helpers to saturation.
- `test_s2_docs_loop.py` phase 5 — migrated the born-dead-on-3rd-cycle cap to the
  saturation regression (a non-saturated target is NEVER born dead).
- `test_cli_envelope.py` — added `docs coverage` to the closed command surface.
- `test_rule_coverage.py` — SCENARIO_COVERED entries for V-COV-01..05 + V-SRC-04.
- `test_api.py` — asserts `/api/coverage`.

## Escalations
None.

---

## Evaluator verdict

**PASS** (fresh adversarial evaluation, HEAD `7052ae4`).

### Independently verified
- **Suite: 510 passed, 0 skipped / 0 xfailed / 0 xpassed** (`.venv/bin/python -m pytest -q -rsxX`; 510 collected). NOTE: the report prose above says "508 passed" — that was the worktree-branch number; on merged `main` it is **510** (matches the mandate). Stale prose only, not a defect.
- **S7 end-to-end under the new floors**: independently rebuilt an S7 project in a persistent dir and ran the REAL CLI binary: `freeze apply --level spine` exit 0 (`ok=true, errors=[]`), `paperproof verify` exit 0, `docs coverage --node NODE-003` returns floor `{required: spine_mechanism, met: true}`. S7 mechanism M **genuinely triangulates**: 2 distinct docs, 2 distinct publishers (BoE T1 + IMF T1 — not two docs from one publisher). No fixture was loosened to pass.

### Supersession (the central risk) — proven GONE
- `grep -rn "meets_evidence_floor|>= *2" src/paperproof/graph src/paperproof/freeze` → **zero code hits** (only explanatory comments). `meets_evidence_floor` / `evidence_binding_counts` absent from all of src/ and tests/.
- MSA-4 (`graph/commands.py:118-128`), V-FRZ-02 (`freeze/apply.py:131-143`), and compiler missing_evidence (`compiler/dry_run.py:52-57`) all delegate to the **single** floor fn `docsdb/coverage.py:_role_floor_met` (via `target_ledger`+`meets_floor`). No duplicated/divergent floor logic.
- Committer verdict-count docs cap **removed**: no `_needs_docs_verdicts` / `_new_target_evidence_since` / `len(verdicts) >= 3` anywhere. `_plan_needs_docs` (`committer/apply.py:346-403`) consults `coverage.target_ledger(...).saturated`. Only committer born-dead reasons are `"saturated"` (V-COV-03 path) and `"bridge cap reached"` (the SEPARATE bridge round cap `_bridge_rounds`, `rounds>=2` — correctly retained).

### Adversarial probes (own fixtures, 20/20 green; drove coverage + msa-check + freeze directly)
- **Role floors**: spine mech with 1 binding → FAILS floor + MSA-4 + freeze(V-FRZ-02). Same-publisher T3/T3 → `triangulated=false`, FAILS floor, freeze reports BOTH V-FRZ-02 and V-SRC-04. T1+distinct-T4 → `triangulated=true`, PASSES floor + MSA-4. Triangulated-but-no-completed-search → counter `no_attempt`, FAILS floor + MSA-4 (proves the counter condition has teeth). Bridge: 2 docs FAILS, 3 distinct docs PASSES. Non-spine fact: 1 EU PASSES, 0 EU FAILS.
- **Saturation vs cap**: fresh (pre-saturation) needs_docs opens a real docs work item and is never born-dead; saturated+floor-unmet → born-dead reason=`saturated` (only reason `check_born_dead_reason` accepts); `is_saturated` matches the docs/17 formula (truth-table probe + fold).
- **Ledger determinism [V-COV-01]**: `build_ledger` byte-identical across two calls on identical canonical state.

### Judgment: the "counter-angle-from-completed-search" derivation
Sound **by delegation to V-SP-02**, with a narrow over-report. `_angle_outcomes` step 1 marks `counter := tried_empty` for ANY completed (fulfilled/not_found) request targeting the node — it does NOT inspect the query_log for an executed/blocked counter qid. For genuine **v2** DocsResults this is safe: `v_sp.check` rejects a v2 result whose plan skips the mandatory counter query (planner always emits one), so "completed v2 request ⟹ counter executed-or-blocked" is a hard, ingestion-enforced invariant. The gap: **cache-fulfilled** (`fulfilled_by="cache"`, zero queries) and **legacy v1** results are NOT covered by V-SP-02, yet still flip counter to `tried_empty`. Proven directly (probe E1): a spine mechanism whose only completed request is a cache hit passes the counter floor; and S7 itself earns its counter floor from a **v1 fake result with no counter query** (`angles.counter=tried_empty`, `academic=no_attempt`). This does NOT let a bogus claim freeze — the floor's real teeth (≥2 bindings, ≥2 distinct docs, independent-publisher triangulation) require genuine evidence a cache hit cannot fabricate, and the counter sub-condition still forces the node to own a completed request. But the ledger's "counter attempted" is a request-existence proxy, not a query_log fact, so it **overstates counter coverage** for non-v2 completions. **Non-blocking.** Recommended hardening (before or after gate/m8, Orchestrator's call): derive counter-attempt from an executed/blocked counter qid in a v2 query_log (or the critic coverage report), and exclude `fulfilled_by="cache"` from the counter derivation.

### Weakened-test audit (diff vs gate/m7-s2-search-orchestra)
No weakening. `test_v_frz` STRICTER (+triangulation, +counter-angle FAIL case, +same-pub-T3 FAIL case). `test_r3_core` test 3 and `test_s2_docs_loop` phase 5 migrated from the removed cap to saturation — the born-dead assertions became the corrected NOT-born-dead behavior (the supersession), plus added ledger/pure-function assertions; old cap tests migrated in place, none silently deleted. `test_v_cdr` note-text only. `test_cli_envelope` (+`docs coverage` to closed surface) and `test_rule_coverage` (+V-COV/V-SRC-04 entries) are additive-stricter. `FakeDocsWorker.per_member` is an opt-in kwarg defaulting to None → prior behavior byte-identical.

### Doc-sync
docs/09 has the `### V-COV` block (V-COV-01..05), V-FRZ-02 rewritten to delegate to the role floor + report V-SRC-04, and V-SRC-04 flipped to ADOPTED. docs/16 triangulation + V-SRC-04 flipped to ADOPTED/BINDING and matches the shipped `triangulated` (branch a: T1/T2 + distinct doc; branch b: 2 independent T3/T4). docs/17 matches shipped code. Surface: `docs coverage [--node]` (CLI, in closed-command test), `/api/coverage` (route + test), ContextPack coverage block (V-COV-02) — nothing beyond docs/17.

### Defect the Orchestrator must fix before tagging gate/m8
None blocking. One non-blocking finding to log: **counter-angle over-report on cache/v1 completions** (see judgment above) — hardening recommended, not gate-blocking.
