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
