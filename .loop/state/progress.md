# Progress — PaperGraph v1 build

Resume point after any compaction/crash: re-read this file + contract.md + log.md.
Do NOT trust a session summary.

## Loop status
- Outer budget: 3 re-entries. Used: 0.
- Current stage: **m1-proof-loop** (attempt 1, cap 4). [m0 PASSED attempt 1]
- Gate tags: gate/m0-foundation.
- m0: 171 tests green; evaluator PASS (independent verify). Contract A1–A7, A24 proven.

## Carried-forward notes for M1 (from m0 evaluator/generator)
- golden scope.period "2020–2023, centered on…" is NOT a parseable year range →
  scope_compatible (V-NODE-03) will fall back to substring matching. Expected per
  docs/01 P6 verbatim copy; M1 committer must handle this gracefully (it does by
  the §0 fallback). No action needed, awareness only.
- CLI stub surface already registered for all 43 commands; M1 replaces the proof/
  queue/expand/validate/commit group stubs with real behavior.
- textutil, ids, clock, serializer, store, snapshot, schemas (all *.v1) are DONE
  and available to import — M1 builds on them, does not re-create them.
- docs edited during m0 (doc-first): docs/09 §0 stoplist "72"→"82"; docs/10 §4
  added --help exemption note. Both shipped in the m0 commit.

## Architecture in use
- Orchestrator (main, Opus) = planner + loop driver; stays lean.
- Generator subagent (Opus, high) builds each milestone's src+tests.
- Evaluator subagent (Opus, high, FRESH each gate) adversarially gates.
- Env: `.venv` (uv, CPython 3.12.13). Gate via `.venv/bin/python -m pytest -q`.

## Stage plan — m0-foundation
Deliverables (docs/10 §3 layout, §7 M0; docs/11 §9 M0 row; contract A1–A7):
- `pyproject.toml` (deps + `[project.scripts] paperproof=paperproof.cli.app:main`, requires-python>=3.12)
- `src/paperproof/schemas/` — ALL *.v1 models + registry (schema_version→class); extra=forbid
- `src/paperproof/textutil.py` — docs/09 §0 exactly (the ONLY tokenizer/counter)
- `src/paperproof/ids.py`, `clock.py` (PAPERPROOF_NOW), canonical serializer
- `src/paperproof/store/jsonl.py` (append/latest_by_id/fcntl/path-safety), `snapshot.py`
- `src/paperproof/scoping/` — topic parser P1–P7 → PaperSpec + Contract; spec build/accept/show
- `src/paperproof/validate/registry.py` + `rules/v_spec.py`, `v_path.py`
- `src/paperproof/cli/` — typer app, FULL closed surface (docs/10 §4); M0 cmds real,
  rest = stub {ok:false, errors:["NOT-IMPLEMENTED"]} exit 1; one JSON envelope always
- tests: unit/{textutil,jsonl_store,snapshot,ids}, contract/{schemas,v_spec,v_path,cli_envelope}
- tests/conftest.py — determinism harness (clock/pp/project/canonical fixtures, docs/11 §3)
- fixtures/{schemas,topics,vrules/V-SPEC-*,V-PATH-*}
Build order: textutil+ids+clock FIRST, then schemas, store, scoping, validate, cli.
Gate: the m0 `feedback_signal.check` (pytest -q + 8 file-presence tests).

## Next actions (M1 — proof loop)
Deliverables: queue/ (leases, events, transitions, unblock/expire sweeps),
prooftask/ (bundle builder + -rN), decision table (pure fn, 24 goldens FIRST),
validate rules V-PR/V-EXP/V-TASK/V-Q/V-COMMIT, committer/ (verdict→action +
admin commits + cascade + bridge wiring + staleness), expander/ ; tests
test_decision_table (24+fuzz), test_v_pr, test_v_exp, test_v_task, test_v_q,
test_v_commit, test_rule_coverage, S1/S4/S5/S6, test_determinism; fakes/ +
scripts/. Gate = m1 feedback_signal.check. on_failure=restart (cap 4).
1. dispatch M1 generator (Opus/high). Emphasize: decision table + 24 goldens
   before committer; bridge wiring (docs/08 B6) exactly; byte-determinism.
2. run M1 gate → gate-reports/m1-proof-loop-attempt1.md.
3. fresh evaluator (must probe: decision-table totality not vacuous; S1 bridge
   edges C→B/D→B actually wired + in spine; determinism byte-level not object-level).
4. on PASS: git tag gate/m1-proof-loop, commit, advance to m2.

## Open doc issues found during build
(none yet)
