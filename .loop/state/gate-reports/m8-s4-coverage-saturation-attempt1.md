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
