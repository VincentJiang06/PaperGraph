# Gate report — m6-s1-search-planning (attempt 1)

Result: **PASS** (worktree build). Full suite **437 passed** (baseline 420 at the
worktree base 967a8cf + 17 new V-SP contract tests). No src changed, no existing
test weakened/deleted, no CLI/schema surface added. `paperproof verify` on an
accepted project = exit 0.

## Base-state finding (important — read first)

The worktree was described as "branched from 967a8cf, which has the S1 adoption
docs" and was expected to have the adoption docs but NOT the S1 implementation.
Two facts diverged from that:

1. The worktree actually checked out at **4e5860a** (the *parent* of 967a8cf),
   i.e. one commit *behind* the intended base — it had neither the adoption docs
   nor any S1 code. I reset the worktree forward to 967a8cf (a descendant of
   4e5860a; safe, isolated) so it carries the binding adoption docs the stage
   requires. My branch is therefore a **linear descendant of main@967a8cf** →
   the Orchestrator's `git merge` is a clean fast-forward.

2. Commit 967a8cf's message says "**No code yet** — this is the adoption +
   build-plan commit". That is inaccurate: 967a8cf already contains a **complete,
   green S1 implementation** (schemas/search.py, docsdb/planner.py,
   validate/rules/v_sp.py, registry + ingest wiring, `docs plan` CLI, the
   docs_worker prompt block, all V-SP fixtures, and tests/unit/test_search_plan.py)
   — 420 tests passing. It contains **no S3-lite code** (the parallel m6b stage
   is correctly absent: no v_src, no document.v2, no `docs source` CLI).

So S1 was ~95% already built in the base. I verified that pre-existing build
against docs/14 + docs/11 §12 + A33–A36 line by line (all sound) and found the
**one missing required deliverable**: `tests/contract/test_v_sp.py`
(T-S1-2 + T-S1-3), which is also an explicit gate criterion
("tests/contract/test_v_sp.py present"). Without it the V-SP fixtures were
**inert** — the rule-coverage meta-test only glob-checks that fixture files
*exist*; nothing ran them through the validator. I added that file (and only
that file). This completes S1's graded test surface.

## What I built

- NEW `tests/contract/test_v_sp.py` (17 tests), mirroring the established
  test_v_dr.py pattern:
  - T-S1-2: parametrized over every `tests/fixtures/vrules/V-SP-0N/{pass_,fail_}*.json`,
    each run through the REAL `v_sp.check(result, plan)`; asserts the named rule
    absent (pass) / present (fail). Covers V-SP-01..05.
  - T-S1-2: per-rule pass_+fail_ presence; `v_sp` no-ops on a v1 result;
    docs_result.v2 round-trips (query_log, no search_log); docs_result.v1 still
    validates under the v1 model (v1 stays readable); v2↔v1 log fields don't cross
    (extra=forbid on both).
  - T-S1-3: hostile fabricated counts (docs_taken 5 > urls_seen 2) → fired ==
    ["V-SP-03"] (isolated); `docs plan --request <DR>` emits the plan and re-emits
    it byte-identically (both the stored `docs/plans/SP-<DR>.json` file and the
    envelope data), with the mandatory counter query present.

## A33–A36 status (verified against the base build + my new test)

- **A33 (T-S1-1)** PASS — pre-existing `tests/unit/test_search_plan.py`: byte-exact
  golden for official_stats (test_search_plan.py:43), CJK per-char frequency
  ranking + determinism (:82), counter-in-every-angle (:52), angle suffix (:62),
  facets/scope fallback (:68). Compiler is doc-faithful: docsdb/planner.py
  ANGLE_SUFFIX (:40), frozen COUNTER_TERMS (:49), mandatory counter (:151-156).
- **A34 (T-S1-2)** PASS — V-SP-01..05 registered (validate/registry.py:68-72),
  exercised for real by NEW test_v_sp.py::test_vsp_fixtures; docs_result.v2
  round-trip + v1-valid-under-v1 (test_v_sp.py:81-105 and test_schemas.py
  generically); rule-coverage meta-test green.
- **A35 (T-S1-3)** PASS — hostile fabricated-counts → V-SP-03
  (test_v_sp.py::test_hostile_fabricated_counts_rejected_by_v_sp_03); `docs plan`
  reprint byte-identical (test_v_sp.py::test_docs_plan_cli_reprint_is_byte_identical).
- **A36 (T-S1-back)** PASS — all prior tests green (437 total, no regression);
  DocsWorker dispatch attaches a compiled plan (docsdb/commands.py:85 in
  `request()`, prompt block in prompts/docs_worker.txt:9-14); V-DR/ingest/cache/
  S2/S3 docs flows intact; docs_result.v1 still parses + validates under v1.

## Doc-sync

None required. The only change is a test file that the docs already call for
(docs/11 §12 T-S1-2 / T-S1-3). No src deviation, no operationalization.

## Gate command note

The worktree has no local `.venv`; the shared repo venv's editable install points
at the main checkout's src. Because my change is **test-only** (git diff --stat vs
967a8cf is empty; the sole delta is the new untracked test file), the standard
post-merge gate `.venv/bin/python -m pytest -q` from the main worktree will collect
and run test_v_sp.py against identical src → 437 green. In-worktree I ran it as
`PYTHONPATH=src .venv/bin/python -m pytest -q` (and confirmed the same result via
the shared editable install).
