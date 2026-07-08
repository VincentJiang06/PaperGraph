# Gate report — m7-s2-search-orchestra (A40–A43)

_Builder attempt body was not present at evaluation time; this file was created by
the fresh Evaluator to carry the verdict. Stage under test: S2 Search Orchestra
(docs/15), merged onto main at HEAD `f92eec5`._

## Evaluator verdict

**FAIL** — a correctness defect in the follow-up path causes silent EVIDENCE
LOSS and violates V-WAVE-01/02 (contract A40 + A41). The full suite is green
(487) and every other probe passes, but a green suite hides this because the
only rule that S2 enforces at runtime is V-WAVE-03; V-WAVE-01/02/04/05 are pure
functions called *only from tests* (with synthetic, already-distinct inputs) and
are NOT swept by `paperproof verify` — so nothing observes the real breakage.

### Verified test count
- `.venv/bin/python -m pytest -q` → **487 passed, 1 warning, 0 skipped, 0 xfailed** (re-run clean).
- S2 subset `tests/{contract,integration}/test_s2_wave.py` → 23 passed.
- `paperproof verify` exits 0 on every wave-built project I drove (probes 4–7) — including the data-loss project, i.e. verify does NOT catch the defect.

### Per-probe results (my own adversarial inputs, real runtime paths)
- **P1 merger determinism/dedup** — PASS. Byte-identical across two runs and across independently reconstructed members; content_hash dup + canonical-URL tracking-param variant collapse to 2 docs; dup EU dropped; canonical_url strips port/frag/{utm_*,gclid,fbclid,ref}/slashes and keeps a real query param; V-WAVE-02 traceability passes honest / fires on an injected untraceable doc.
- **P2 verdict is CODE** — PASS. all-yes+primary→sufficient@r1; primary=no→followup@r1 but sufficient@r2 (waived at R_MAX); no_attempt / disconfirming=no→followup@r1→closed@r2; tried_* + n/a→sufficient. Exhaustive 576-combo sweep: R_MAX=2 NEVER yields `followup` (hard halt). followup_specs = 1/no_attempt + 1/expected_source with suggested_query→hint.
- **P3 hostile critic** — PASS. read-only complete form passes; smuggled documents/evidence_units (top-level AND nested) → V-WAVE-03; expected_sources>3 → V-WAVE-03; missing mandatory angle / out-of-enum value → V-WAVE-03.
- **P4 one DRES per wave** — PASS. Full fan→merge→ingest yields exactly one DRES; all ingested docs carry it; per-member files remain in agent_outputs; merged file written; pre-existing single docs item superseded (cancelled).
- **P5 the ingest.py seam** — PASS (fix is correct — see below).
- **P6 non-fan back-compat** — PASS. `docs wave --request` (no --fan) → single official_stats member; a plain reactive `docs request` + drain still ingests as the pre-S2 single loop (1 DRES, no wave record).
- **P7 R_MAX close** — PASS at the level the existing tests check (closed@R_MAX, round==2, every follow-up cites origin, no round-3, one DRES) — but see the defect: the follow-up members it opens collide.

### Judgment on the ingest.py seam fix — CORRECT (not a paper-over)
`_archive_result(…, raw_result)` is threaded correctly and passed at BOTH call
sites: `ingest_result` (ingest.py:206, `raw` = the docs_result) and
`ingest_merged` (ingest.py:338, `raw` = the merged file). I independently drove a
merged wave whose docs sit on a web domain (`blocked.example`) with a 403/forbidden
query-log note naming the domain, and proved the **merged path** learns a
`SourceProfile` with `blocked_direct=True`, tier `T1_official`, seen_count>0, and
ingests `document.v2` records whose `provenance.tier` is denormalized from the
registry. A control (identical wave, no block note) leaves `blocked_direct=False`
— which is only possible if `raw` (carrying the query_log) is genuinely threaded
to `registry.learn`. So the union S3-learns-from-merged-ingest the merge intended
is real, and `verify`'s V-SRC provenance sweep stays clean.

---

## DEFECT (BLOCKER) — follow-up members reuse round-1 output paths ⇒ evidence loss; V-WAVE-01/02 violated

**Assertion.** A wave's member outputs must be pairwise-distinct declared paths
(docs/15 §Rules V-WAVE-01; docs/09 §V-WAVE "checked across the wave lifecycle";
contract A41 "member outputs pairwise-distinct"). The shipped follow-up path
produces NON-distinct member outputs, silently overwriting round-1 committed
member result files, so round-1 evidence for any reopened angle never reaches the
merge/ingest.

**Defect (file:line).**
- `src/paperproof/docsdb/wave.py:308` — `_open_member` derives the output path from `(request_id, angle)` ONLY: `output = f"agent_outputs/docs_results/{request_id}.{angle}.docs_result.json"`. The round is not in the path.
- `src/paperproof/docsdb/wave.py:532-535` — `resolve_critic` opens each follow-up via `_open_member(..., spec["angle"], next_round, ...)`, reusing the angle. A no_attempt-angle follow-up reopens that angle; an expected_source follow-up is hardcoded to `angle="official_stats"` (`wave.py:233-234`) — which the round-1 fan ALWAYS contains. Both therefore reuse a round-1 member's exact output path.
- `src/paperproof/docsdb/wave.py:427-439` — `_collect_member_results` reads `item["output_files"][0]` once per member with no path-dedup, so the shared (overwritten) file is read twice, and round-1's distinct content is unrecoverable.
- Not enforced anywhere: `validate/rules/v_wave.py:32 check_member_paths` (V-WAVE-01) and `check_merge`/`check_wave_rounds`/`check_single_dres` are called only from `tests/` (with synthetic distinct paths); `src/paperproof/verify.py` schema-checks `docs/waves.jsonl` but runs no V-WAVE-01/02/04/05 sweep. So the invariant docs/09 claims is "checked" is not checked.

**Minimal repro.** `/private/tmp/.../scratchpad/ev_s2_dataloss.py` (a worker that
returns distinct content per angle+invocation; a critic that returns one no_attempt
angle + one expected_source in round 1, all-covered in round 2):
```
members:
  r1 official_stats  None                     -> …/DR-001.official_stats.docs_result.json
  r1 industry        None                     -> …/DR-001.industry.docs_result.json
  r2 industry        angle:industry           -> …/DR-001.industry.docs_result.json      ← SAME
  r2 official_stats  expected_source:BLS CPS  -> …/DR-001.official_stats.docs_result.json ← SAME
INGESTED tags:  ['ACADEMIC-1','COUNTER-1','INDUSTRY-2','OFFICIAL_STATS-2']
EXPECTED     :  [...,'INDUSTRY-1','INDUSTRY-2','OFFICIAL_STATS-1','OFFICIAL_STATS-2']
>>> LOST round-1 evidence: ['INDUSTRY-1','OFFICIAL_STATS-1']
```
`OFFICIAL_STATS-1` was found by a round-1 member the critic marked **covered**
("yes"); it is silently dropped. `check_member_paths` over the wave's ACTUAL
member output_files fires **V-WAVE-01** (`ev_s2_collision.py`: 6 members, 4
distinct paths). `verify` still exits 0. This also breaks V-WAVE-02's "every
merged doc/EU traces to **exactly one** member" (two members share one physical
file) and docs/15's "per-member results stay in agent_outputs as provenance" (the
round-1 provenance file is overwritten).

**Why the suite misses it.** `FakeDocsWorker` returns identical content for every
member (keyed by request_id / "*"), so the overwrite is content-invisible in
`test_s2_wave.py`; and no runtime/verify code path calls `check_member_paths`.

**Minimal fix direction (for the Orchestrator, not applied here).** Make the member
output path (and ideally the member's identity used by `_collect_member_results`)
unique per round/origin — e.g. `…/{request_id}.{angle}.r{round}.docs_result.json`
for round>1 (or include an origin discriminator) — and add a V-WAVE-01 sweep to
`verify` (and/or a runtime `check_member_paths` call in `start_wave`/`resolve_critic`)
so the "checked across the wave lifecycle" claim is real. Add a regression test
where members carry distinct content and a follow-up reopens `official_stats`.

---

## Weakened-test audit & doc-sync — clean (one cosmetic nit)
- Diff `tests/` vs `gate/m6b-s3-lite-source-registry` is **additive**: new `test_s2_wave.py` (contract+integration), new `FakeCriticWorker`/`drive_wave`, two schema fixtures. The only edits to pre-existing files TIGHTEN coverage: `test_cli_envelope.py` adds `docs wave` to CLOSED_COMMANDS; `test_rule_coverage.py` adds V-WAVE-01..05; `tests/fakes/workers.py` `FakeDocsWorker` now prefers the angle plan (`SP-<DR>-<angle>`) — a needed extension, not a loosened assertion. No prior docs/proof test relaxed or deleted.
- Schema-enum widenings are within docs/15's adoption: `QueueName` gains `critic_queue`, `target_type` gains `wave`, and `search_wave.v1`/`coverage_report.v1` are registered.
- Doc-sync present and consistent: docs/00 §"Search Program Adoption — S2" + line 70; docs/09 §V-WAVE (01–05); docs/10 §4 `docs wave` row; docs/11 §12 T-S2-1..4; docs/15 status ADOPTED/BINDING.
- **Cosmetic nit (non-blocking):** `test_rule_coverage.py` SCENARIO_COVERED values name tests that don't exist verbatim (e.g. `test_wave_member_paths_distinct` vs the real `test_v_wave_01_member_paths_distinct`); the meta-test only checks rule-id membership so it passes, but the descriptions are inaccurate. And, tellingly, V-WAVE-01/02/04/05 are marked "scenario-covered" while having no runtime/verify enforcement — the coverage map records tests, not enforcement.

**Gate decision: FAIL.** Fix the follow-up output-path collision (and give
V-WAVE-01/02 a real runtime or verify check) before tagging `gate/m7`.

---

## Attempt 2 fix (2026-07-08) — silent evidence loss on follow-up rounds

**Status: PASS.** `.venv/bin/python -m pytest -q` = **489 passed** (487 + 2 new).
Real binary `python -m paperproof verify` on a wave-built project: exit 0 clean;
exit 3 with `errors=['V-WAVE-01']` on a seeded path collision. No commit/tag.

### Root cause (confirmed)
Every follow-up member reused a round-1 member's output path — the path was keyed
only by `(request_id, angle)` with no round discriminator, and every follow-up is
opened at an already-fanned angle (`no_attempt` reopens that angle;
`expected_source` was hardcoded to `official_stats`). The round-2 DocsWorker
overwrote the committed round-1 file; `_collect_member_results` then read the
overwritten file (twice), so round-1 evidence was unrecoverable. V-WAVE-01/02
were pure functions called ONLY from tests with synthetic distinct inputs, and
`FakeDocsWorker` returned identical content per member, so the overwrite was
content-invisible.

### Part 1 — unique member paths across the whole wave lifecycle (docs/15)
- `src/paperproof/docsdb/wave.py` new `member_output(request_id, angle, round, origin)`
  (+ `_SLUG_RE`): round-1 members keep the bare
  `agent_outputs/docs_results/DR-x.<angle>.docs_result.json`; a round>1 member gets a
  `.r<round>.<origin-slug>` discriminator so it never reuses — hence never overwrites —
  a round-1 path, and two follow-ups (reopened angle vs expected_source) never collide.
- `wave.py` `_open_member` now calls `member_output(...)` instead of the angle-only path.
  `_collect_member_results` (unchanged) reads each member's own distinct file.
- Doc-sync: `docs/15` §Wave expansion (round>1 path scheme) + §Operationalization
  (path discriminator + the new verify sweep).

### Part 2 — make V-WAVE real, not test-only (`src/paperproof/verify.py`)
- New `_wave_check(paths)`, wired into `run()` before `_crossref`. For every wave it
  sweeps **V-WAVE-01** (member output paths pairwise-distinct via
  `v_wave.check_member_paths`) — a collision at rest → exit 3. For a **closed** wave
  with a merged file it also sweeps **V-WAVE-02** (`v_wave.check_merge`: merge
  determinism + every merged doc/EU traces to a member). Added `import json`.
  Corruption guard only — flags genuine collisions, skips mid-lifecycle merges.

### Part 3 — regression tests (`tests/integration/test_s2_wave.py`)
- `test_followup_reopening_official_stats_preserves_round1_evidence`: drives a wave
  with content-DISTINCT members (per-member quote keyed by work_item_id) and a round-2
  follow-up that REOPENS `official_stats` via an expected_source; asserts round-1 and
  round-2 members declare distinct paths AND every member's unique quote survives into
  the single ingested merged set. Red on the bug (round-1 official_stats quote lost),
  green after the fix.
- `test_verify_flags_path_colliding_wave_v_wave_01`: seeds a wave whose two members
  declare the same output path; asserts `paperproof verify` exits 3 with V-WAVE-01
  (and exits 0 on the clean wave). Red before Part 2, green after.
- `tests/fakes/workers.py`: `FakeDocsWorker` gains an **opt-in** `per_member`
  callable (default None → unchanged request_id/"*" lookup) so a test can give each
  member content-distinct output. No existing behaviour/assertion changed.

### Untouched (as required)
- `ingest.py` `_archive_result(..., raw_result)` seam untouched.
- No existing test weakened/deleted (only additive: 2 tests + 1 optional worker param).
- No CLI/schema surface added beyond docs/15.

---

## Re-verification (fix by a different agent; independently checked as the checker)

**PASS.** The data-loss blocker is genuinely resolved and V-WAVE-01/02 are now
real (runtime, not test-only). No new defect; one minor non-blocking hardening
note. I re-ran every relevant probe against the patched working tree (HEAD still
`f92eec5` + uncommitted fix).

### The fix (what changed)
- `src/paperproof/docsdb/wave.py`: new `member_output(request_id, angle, round, origin)` (wave.py:307-320). Round-1 members keep the bare `DR-x.<angle>.docs_result.json`; a round>1 member gets a `.r<round>.<origin-slug>` discriminator (origin slugged to `[a-z0-9-]`). `_open_member` (wave.py:327) now uses it.
- `src/paperproof/verify.py`: new `_wave_check` (verify.py:111-149) called from `run()` (verify.py:161) — sweeps **V-WAVE-01** (pairwise-distinct member output paths, over the wave's work-item output_files) on every wave, and **V-WAVE-02** (recompute-merge + traceability) on every *closed* wave.
- `docs/15` §Wave expansion + §Operationalization: documents the `.r<round>.<origin-slug>` scheme and the verify sweep.
- `tests/`: +2 additive integration tests + an opt-in `per_member` hook on `FakeDocsWorker`.

### Re-checked, each independently proven
1. **No more data loss (my own repro).** `ev_s2_dataloss.py` (distinct content per member; round-2 reopens both `industry` via no_attempt and `official_stats` via expected_source): all 6 members now declare **6 distinct** paths (`…industry.r2.angle-industry…`, `…official_stats.r2.expected-source-bls-cps…`); the ingested set contains ALL of `{OFFICIAL_STATS-1, OFFICIAL_STATS-2, INDUSTRY-1, INDUSTRY-2, ACADEMIC-1, COUNTER-1}` — **LOST = []** (was `['INDUSTRY-1','OFFICIAL_STATS-1']`). `check_member_paths` over the real member outputs = PASS.
2. **verify V-WAVE-01 is REAL, in `verify.py` code (not a test).** Seeded a wave whose two members declare one shared output path → `paperproof verify` **exit 3 with V-WAVE-01**; a clean driven wave (incl. an r2 followup) → **exit 0**. Confirmed by source inspection that `verify.run()` calls `_wave_check`, which calls `check_member_paths` (V-WAVE-01) and `check_merge` (V-WAVE-02). V-WAVE-02 sweep is not a no-op: tampering a closed wave's stored merged file with an untraceable doc → **exit 3 with V-WAVE-02** (clean → exit 0).
3. **Suite = 489 passed, 0 skipped / 0 xfailed** (487 + the 2 new regression tests). `tests/` diff vs `gate/m6b-s3-lite-source-registry` is additive-only: the sole edits to pre-existing files are `test_cli_envelope.py` (+1 `docs wave`, tightening) and `tests/fakes/workers.py` (opt-in `per_member=None` hook — every existing caller unchanged); no prior docs/proof assertion loosened or deleted. The two new tests are exactly the right regressions (`test_followup_reopening_official_stats_preserves_round1_evidence`, `test_verify_flags_path_colliding_wave_v_wave_01`).
4. **ingest.py seam untouched.** `git diff src/paperproof/docsdb/ingest.py` = 0 lines; `_archive_result(…, raw)` still passed at BOTH call sites (ingest.py:206 and :338). Re-ran P1–P7: all green.
5. **Doc-sync.** docs/15's `agent_outputs/docs_results/DR-x.<angle>.r<round>.<origin-slug>.docs_result.json` matches `member_output`'s output byte-for-scheme; the verify-sweep note is documented.

### Minor, non-blocking (hardening opportunity, not a gate blocker)
`followup_specs` derives a round-2 member's origin from the critic's
`expected_source.name`, and `check_critic` (V-WAVE-03) does not dedup expected_source
names. Two expected_sources with an IDENTICAL name yield two round-2 members with
the same origin → the same `.r2.expected-source-<name>` path (probe
`ev_s2_dupname.py`: 6 members, 5 distinct). This is (a) pre-existing (the old code
collided on EVERY expected_source), (b) requires a malformed/adversarial critic,
and (c) **caught by the new verify sweep** — `paperproof verify` returns exit 3
with V-WAVE-01, so it cannot pass a verify gate as silent corruption. It is
consistent with this system's detect-at-rest guarantee model. Optional harden:
uniquify the origin (append an index) in `followup_specs`, or reject duplicate
expected_source names in `check_critic`. The docs/15 line "Origins are pairwise-
distinct within a round" is very slightly overstated for this narrow case.

**Gate decision: PASS.** The blocker is resolved; V-WAVE-01/02 are enforced by
`verify`; suite green (489), additive-only; seam intact; docs synced. Clear to
tag `gate/m7` (completing Stage A). Recommend the Orchestrator file the minor
duplicate-expected-source-name hardening as a follow-up, not a blocker.
