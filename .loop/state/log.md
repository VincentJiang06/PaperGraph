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
