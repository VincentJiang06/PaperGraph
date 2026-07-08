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

---

## Evaluator verdict

Fresh adversarial Evaluator, main working tree @ HEAD 6072f39 (437 tests). I did
not trust the shipped fixtures — every probe below uses inputs I constructed.

**Verdict: FAIL — one doc-sync defect (doc-only fix). The S1 *implementation* is
fully correct: I independently re-proved A33–A36 end to end. The gate cannot
close as-is because a binding deviation from `docs/` was shipped undocumented,
and the m6 gate + CLAUDE.md both require the doc amendment in the same change.
The maker report's "Doc-sync: None required" is wrong.**

### Independently verified (all green)
- `.venv/bin/python -m pytest -q` in a clean shell → **437 passed**, 1 warning.
  `--collect-only` → **437 collected**, nothing skipped/xfailed. S1 subset
  (test_search_plan + test_v_sp + test_rule_coverage) = 35 passed.
- `.venv/bin/python -m paperproof verify` on a project I built through the full
  v2 flow (init → spec → seed → `docs request` → claim → `docs ingest-result` a
  not_found docs_result.v2) → **exit 0, ok:true**.

### Per-probe (my own inputs, not shipped fixtures)
- **Compiler determinism**: same request compiled twice → byte-identical (ASCII
  and CJK). PASS.
- **CJK need**: `人工智能 就业 人工智能` → core `['人','工','智','能','就','业']`
  (per-char, freq-ranked, ≤6 cap), region `中国` casefolded into scope, counter
  present, recompile byte-identical. PASS.
- **Core facet law**: ≤6 cap honored (8 distinct tokens → first 6); tie =
  first-occurrence; scope token `usa` removed from core; freq-then-firstocc order
  (`beta beta alpha…` → `['beta','alpha',…]`). Matches docs/14 formula + planner.py
  operationalization block. PASS.
- **Change one need token** → plan bytes differ. PASS.
- **Counter mandatory**: present + correct suffix (`decline criticism`) for ALL
  five angles incl. non-counter (news/academic/industry). With 12 hints the plan
  caps at 8 queries and the counter is FORCED into Q8 (planner.py:144-156) — it
  survives the cap, texts stay distinct. PASS.
- **Each V-SP rule truly enforces** (hand-crafted violating + clean v2, run
  through the REAL `v_sp.check`): V-SP-01 (missing qid / dup qid / exec=false
  w/o blocked+note), V-SP-02 (counter skipped, counter exec=false-not-blocked),
  V-SP-03 (docs>urls; docs present w/o productive), V-SP-04 (not_found w/
  unexecuted; not_found w/ productive), V-SP-05 (plan=None; request_id mismatch).
  Every violation returns THAT rule id; every clean case returns []. Extra `X1`
  entries allowed; v1 result no-ops. PASS.
- **Rule wired into the docs validate path (not just registry)**: driving the CLI,
  a hostile v2 (docs_taken 9 > urls_seen 2) is rejected with `['V-SP-03']` through
  BOTH `validate docs-result` AND `docs ingest-result` (ingest.py:168-170 gates
  v_sp on v2 only); a clean v2 passes; deleting the plan file → `['V-SP-05']`. PASS.
- **Plan attached at dispatch**: compiled + written to the deterministic
  `docs/plans/SP-<DR>.json` at BOTH dispatch sites — `docs request`
  (commands.py:85) and the Committer needs_docs path (`_wire_docs`,
  apply.py:539). Enforced at ingest by V-SP-05, so an unplanned v2 cannot pass.
  (Note: `work_item.bundle` stays None — the plan is discovered by canonical path,
  same convention as every other worker prompt, which no code renders; the teeth
  are V-SP-05. Acceptable, matches the codebase pattern.) PASS.
- **v2 back-compat**: docs_result.v1 still validates under the v1 model; v2↔v1 log
  fields can't cross (extra=forbid). **V-DR-06 both branches**: v1 not_found w/
  empty `search_log` → V-DR-06; v2 not_found w/ empty `query_log` → V-DR-06;
  each clean when its log is non-empty (v_dr.py:92-98). PASS.
- **CLI reprint**: `docs plan --request` twice → byte-identical stored file AND
  envelope data. PASS.
- **Re-derived goldens by hand from docs/14 §Rules**: V-SP-01 and V-SP-03 code
  matches text exactly; the official_stats golden in test_search_plan.py is
  byte-correct when re-derived from the formula block + docs/09 §0 tokenizer.
- **Weakened-test audit** (diff vs 4e5860a == gate/m5-r3-behavior): only two
  pre-existing test files touched — test_cli_envelope.py (+`docs plan` to the
  closed list, additive) and tests/fakes/workers.py (additive v2 emission; honest
  query_log by default, hostile still scriptable). test_v_dr / test_s2 / test_s3 /
  test_rule_coverage byte-unchanged. No docs assertion weakened. PASS.

### FAIL finding — F1 (doc-sync, blocking; doc-only remediation)
**Assertion**: CLAUDE.md — "checks are the V-* rules in docs/09-verification.md"
and "Any deviation from docs/ requires updating the doc in the same change"; the
m6 gate's Doc-sync clause. docs/00's own binding adoption entry promises the
docs/09 amendments.

**Defect 1** — `docs/09-verification.md` has **no `### V-SP` block**. `grep -c
'^### V-SP ' docs/09-verification.md` → **0**, while `registry.py:68-72` +
`validate/rules/v_sp.py` ship and enforce V-SP-01..05. Every other registered
family has a docs/09 block, including V-SWEEP which correctly got one when added
in m5 (docs/09:75). `docs/00-overview.md:242` explicitly states "V-SP-01..05 join
the registry (**docs/09 gains a V-SP block**)" — the promise was not kept. The
five enforced rules are absent from the doc CLAUDE.md names as authoritative for
checks. (Repro: `grep -c '^### V-SP ' docs/09-verification.md` → 0.)

**Defect 2** — `docs/09-verification.md:219` V-DR-06 still reads only
"…search_log non-empty", not re-expressed for v2's query_log, although
`docs/00-overview.md:236` promises "V-DR-06's 'search_log non-empty' is
re-expressed on v2 as 'query_log non-empty'" and `v_dr.py:95-98` implements the
v2 branch. The authoritative check text no longer matches the code for a v2
result. (Repro: read docs/09:219 vs v_dr.py:92-98.)

**Minimal remediation** (no src/test change): add a `### V-SP (search-plan
accounting, S1 — docs/14)` block to docs/09 with V-SP-01..05, and amend the
docs/09:219 V-DR-06 line to note "search_log (v1) / query_log (v2) non-empty".
Both are pure doc amendments; re-run is unaffected (437 stays green).

### Bottom line
Behaviour is sound — A33–A36 all independently reproduced with adversarial
inputs; no regression; no weakened assertion; verify green. The single blocker is
the undocumented deviation in docs/09 (an interruption leftover: code enforces
rules the authoritative check doc omits, and docs/00 promised the block). Fix
docs/09 (F1) in the same change, then this gate is a PASS.
