# Log — append-only, one line per operation

## [2026-07-07] loop-init | created .venv (uv, py3.12.13), seeded contract/progress/log; system py3.9 too old, using uv venv
## [2026-07-07] m0-start | dispatching M0 generator subagent (Opus/high)
## [2026-07-07] m0-gen | M0 generator: 171 tests green, install clean
## [2026-07-07] m0-eval | fresh evaluator PASS (independent verify: textutil/rules/CLI/golden/schemas/store/determinism)
## [2026-07-07] m0-docfix | docs/09 stoplist 72->82; docs/10 --help exemption note; textutil comment 72->82
## [2026-07-07] m0-gate | GATE PASS, tagging gate/m0-foundation, advancing to m1
## [2026-07-07] m1-gen | M1 generator: 303 tests green (171 M0 + 132 M1)
## [2026-07-07] m1-eval1 | evaluator FAIL: F1 hollow V-COMMIT-04 replay (tautological); rest sound
## [2026-07-07] m1-fix | attempt2: enrich CommitDecision actions -> genuine replay; wire V-EDGE-02; apply doc-syncs
## [2026-07-07] m1-fix-done | 312 tests green; genuine replay + V-EDGE-02 live
## [2026-07-07] m1-eval2 | evaluator PASS attempt2 (independent: corrupt action->False, in-window line->False, V-EDGE-02 live, determinism intact)
## [2026-07-07] m1-gate | GATE PASS; tagging gate/m1-proof-loop; advancing to m2
## [2026-07-07] m2-gen | M2 generator: 335 tests green (+23 docsdb/needs_docs)
## [2026-07-07] m2-eval | evaluator PASS (16 probe tests: cache=no-workitem, quote fabrication rejected, dedup, born-dead cap, S3 cascade)
## [2026-07-07] m2-gate | GATE PASS; tagging gate/m2-docs; advancing to m3
## [2026-07-07] m3-gen | M3 generator: 363 tests green (+28 freeze/compiler/audit/trace)
## [2026-07-07] m3-eval | evaluator PASS (independent: msa-check conditional, MSA-9 fires, gap detection real, audit earned, trace to raw file, freeze refusals); N1 non-blocking (verify crossref gap)
## [2026-07-07] m3-n1 | closing N1: verify resolves evidence_bindings + duplicate_of (additive, docs/09 §3)
## [2026-07-07] m3-n1-done | 367 green; verify now resolves evidence_bindings+duplicate_of (docs/09 §3); EU-999 repro exits 3; S7 clean
## [2026-07-07] m3-gate | GATE PASS; tagging gate/m3-endgame; advancing to m4
## [2026-07-07] m4-gen | M4 generator: 375 green (+8 db/ui/S8); shipped 4KB cytoscape stub
## [2026-07-07] m4-cyto | orchestrator vendored REAL cytoscape 3.30.2 (373KB, unpkg); 375 still green
## [2026-07-07] m4-eval | evaluator PASS (index-not-JSONL proved, idempotent rebuild, S8 exit-3 x13 readers, six questions real)
## [2026-07-07] m4-cleanup | N1 project status real MSA (+2 guard tests, 377 green); N2/N3 doc drift aligned (docs/12 vanilla-JS, stale-masks-corrupt note)
## [2026-07-07] final-fresh-clone | FAILED first: .gitignore db/ swallowed src/paperproof/db; fresh clone ModuleNotFoundError
## [2026-07-07] final-gitignore-fix | scoped ignore to data/**/db/; committed swallowed db pkg; fresh clone RE-RUN 377 green (commit)
## [2026-07-07] final-eval | final-audit PASS: fresh-clone 377 from clone, weakened-test hunt clean, rules faithful, invariant sweep genuine
## [2026-07-07] polish | closed 4 low findings (commit_queue FIFO-by-validation-time docs/05, wheel build, trace regex, text_path null); 381 green; wheel ships prompts+ui/static
## [2026-07-07] polish-note | polish subagent overstepped + reverted loop-state files; bookkeeping repaired by orchestrator; code fixes intact
## [2026-07-07] loop-complete | all 5 milestones + final-audit PASS; 381 green from fresh clone; wheel shippable; A26 live smoke = human node
## [2026-07-08] r3-core | code caught up to r3 on the four basic bugs: V-PATH-04 three clauses (T-r3-1), H10->verify snapshot-EOF (T-r3-2), cache DRES-only + verdict-based cap + evidence-arrival staleness + REQUESTED-U-top12 packs (T-r3-3/6 core), event detail (T-r3-8), template sync (T-r3-10 blocks). 386 green.
## [2026-07-08] r3-core-remaining | NOT done (deliberate, behavior upgrades): T-r3-4 (>=2-binding floors), T-r3-5 (sweep gate), T-r3-7 (validate-from-claimed), T-r3-9 (--auto-rebuild), T-r3-10 drift test.
## [2026-07-08] m5-start | loop re-entered at stage m5-r3-behavior; planned A28-A32 (T-r3-4/5/7/9/10); baseline 386 green @ 6072f39; dispatching Generator (Opus/high)
## [2026-07-08] m5-gen | Generator: 399 green (+13 additive); ONE shared floor fn (A28), V-SWEEP-01 rule+gate (A29), implicit-complete proof+docs (A30), ui --auto-rebuild (A31), template drift test (A32); doc-synced docs/04/09/10
## [2026-07-08] m5-eval | fresh Evaluator PASS: 399 re-run clean, 5 probes reproduced with own fixtures, weakened-test audit clean, T-r3-7 docs-path sound; F1 = docs/05 stale on docs implicit-complete path
## [2026-07-08] m5-f1 | Orchestrator reconciled docs/05 §Validation Gate + complete row (validate result=proof, docs ingest-result=docs, validate docs-result=dry check); 399 still green
## [2026-07-08] m5-gate | GATE PASS; code now fully caught up to spec r3; tagging gate/m5-r3-behavior
## [2026-07-08] m5-push | pushed main 6072f39..4e5860a + tag gate/m5-r3-behavior to GitHub origin (VincentJiang06/PaperGraph)
## [2026-07-08] m6-adopt | user directive: complete whole project. Adopted search program S1 (docs/00 entry, docs/14 status→binding, docs/11 §12 worklist). Building set-by-set: m6=S1, m7=S2, m8=S3-lite (Stage A/v1.1); S4/S5 scope fork deferred to Stage A gate.
## [2026-07-08] m6-start | stage m6-s1-search-planning planned (A33-A36); baseline 399 @ gate/m5-r3-behavior; key risk docs_result v1->v2; dispatching Generator (Opus/high)
## [2026-07-08] m6-parallel | user: go faster w/ parallel subagents. Read docs/17(S4)/18(S5): S4 supersedes m5 flat floor (v1.2), S5 needs vendored embedding model (v2 escalation). Target = Stage A (S1+S2+S3-lite, v1.1, no new deps). Adopted S3-lite (docs/00,16,11). Wave 1 = S1 || S3-lite in worktrees; Wave 2 = S2; then S4/S5 fork to user.
## [2026-07-08] m6-s1-provenance | DISCOVERY: the interrupted first m6-s1 generator had written ~95% of S1 into the MAIN tree; my `git add -A` swept it into 967a8cf (msg wrongly said "no code yet"). Verified via diff/reflog: 4e5860a had no S1 code; 967a8cf NOT pushed. Benign — legit generator output.
## [2026-07-08] m6-s1-merge | merged worktree S1 agent's test_v_sp.py (V-SP fixtures were INERT — rule-coverage only checks files exist); 437 green, 17 V-SP tests now run.
## [2026-07-08] m6-s1-eval | fresh Evaluator: impl fully correct (A33-A36 re-proven, no interruption leftovers in code), but FAIL on F1 doc-sync: docs/09 missing ### V-SP block + V-DR-06 not v2-expressed (both promised by docs/00). Fixed docs/09 (doc-only, 437 stays green) → PASS.
## [2026-07-08] m6b-s3-done | S3-lite generator PASS in worktree (419, +20). Base was 4e5860a (stale) so it wrote its own adoption docs → conflicts w/ main's on merge. Manifest received; merging next.
## [2026-07-08] m6-s1-gate | S1 doc-sync F1 fixed (docs/09 V-SP block + V-DR-06 v2); 437 green; tagged gate/m6-s1-search-planning; pushed GitHub (c51792a).
## [2026-07-08] m6b-merge | merged S3-lite onto main (10 conflicts, all keep-both). SEAM FIX: S1's v2 DocsWorker dropped the v1 search_log 403 note S3's registry-learning needs -> FakeDocsWorker now carries a search_log block note into the v2 query_log as a blocked X-id extra. 457 green. Merge ed04781 (NOT yet gated/pushed).
## [2026-07-08] m7-adopt | adopted S2 (docs/00 entry, docs/15 status, docs/11 §12 worklist, contract A40-A43). Launching S2 generator (worktree) + S3 evaluator in parallel.
## [2026-07-08] m6b-gate | fresh Evaluator PASS: 457 verified, 8 probes reproduced, seam fix judged LEGITIMATE (mirrors real DocsWorker X-id contract, flows through prod code), 0 regressions, V-SRC-04 absent, no defects. Marking A37-A39; tagging gate/m6b; pushing.
## [2026-07-08] m7-merge | S2 merged onto main (divergent base, 10 union conflicts). Integration agent CAUGHT a silent auto-merge defect I mis-assessed: S3's `raw`-dependent learn line landed inside S2's refactored _archive_result (NameError, 11 red). Fixed by threading raw through the helper. 487 green. Merge f92eec5.
## [2026-07-08] m7-eval1 | fresh Evaluator FAIL: real DATA-LOSS bug (all 30 tests missed it) — follow-up wave members reuse round-1 output paths (wave.py:308 path keyed only by request_id+angle; :532-535/:233-234 followups hardcoded official_stats), overwriting committed results; V-WAVE-01/02 only called from tests, verify never sweeps them. Ingest seam fix confirmed correct. Dispatching fix (attempt 2).
## [2026-07-08] m7-fix2 | attempt-2 fix (fresh agent, on main): unique round>1 member paths (wave.py member_output .r<round>.<origin>), V-WAVE-01/02 now swept by verify (real, exit 3 on collision), +2 regression tests; doc-synced docs/15. 489 green. ingest seam untouched.
## [2026-07-08] m7-eval2 | Evaluator RE-VERIFY PASS: LOST=[] (was 2 dropped), 6 distinct member paths, verify exit-3 on seeded collision, 489 green additive-only. Clear to tag gate/m7. FOLLOW-UP (non-blocking, caught-at-rest by verify): check_critic doesn't dedup expected_sources names → dup-named would collide on .r2 path; uniquify origin or reject dup names later.
## [2026-07-08] m7-gate | GATE PASS — Stage A (v1.1: S1+S2+S3-lite) COMPLETE. Tagging gate/m7-s2-search-orchestra; pushing.
