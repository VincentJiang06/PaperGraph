# Deletion manifest — reorganize-logic rebuild (2026-07-09)

**Nothing in this manifest has been deleted.** Every entry is a proposal;
you approve (or reject) per file. Git is the safety net either way.

The replacement layer is in place and verified: `docs/contracts/architecture.md`
(protocol-wiring matrix), `structure.md` (module map), `interfaces.md`
(408 public symbols, `verify_contracts.mjs` gate **PASS**, coverage 1.000),
plus the wiring fixes + drift guards landed in the same change
(V-CDR-03 enforcement, `tests/contract/test_wiring.py`).

## A. Retire wholesale — superseded by the new contracts + code/tests

| File | Reason |
|---|---|
| `docs/00-overview.md` | System thesis + component map re-derived into `architecture.md`; its normative changelog is history, not contract — git history preserves it. |
| `docs/02-logic-graph.md` | Node/edge/lifecycle/spine semantics live in `schemas/graph.py`, `graph/model.py`, and the V-NODE/V-EDGE/V-GRAPH rule modules + their contract tests; boundaries in `architecture.md`. |
| `docs/03-proof-machine.md` | The ladder/decision table is code (`committer/decision_table.py`, 26 golden fixtures) and the worker contract is the template itself (`prompts/proof_worker.txt`, drift-guarded). |
| `docs/04-docs-database.md` | Ingest/memoization/pack semantics live in `docsdb/` + V-DR/V-SP tests; wiring matrix covers every artifact. |
| `docs/05-workflow-and-queue.md` | The 11-state table is `queue/engine.py LEGAL` (replay-verified by `v_q`); pipeline order is in `architecture.md`. |
| `docs/06-compiler-and-audit.md` | Freeze/dry-run/draft-map/prose/audit semantics live in `freeze/`, `compiler/`, `audit/` + V-FRZ/V-CDR/V-PROSE tests. |
| `docs/07-runtime-and-tooling.md` | Storage layout is `paths.py`; ids are `ids.py`; roles + dispatch flow are in `architecture.md`. |
| `docs/08-module-contracts.md` | The boundary layer this rebuild replaces most directly: single-writer table + wiring matrix in `architecture.md`/`structure.md`, all gate-checked. |
| `docs/13-search-program.md` … `docs/18-semantic-retrieval.md` (six files) | The S1–S5 program is fully implemented; plans/waves/tiers/ledger/semantic are code (`docsdb/planner|wave|registry|coverage`, `db/semantic`) with V-SP/V-WAVE/V-SRC/V-COV/V-SEM contract tests; adoption history is git history. |

## B. Retire with a required companion change (approve = I do the companion in the same commit)

| File | Blocker | Companion change |
|---|---|---|
| `docs/01-topic-and-scoping.md` | Topic-file authoring guide (9 sections, P1–P7) is USER-facing input documentation, not just contract. | Extract a short `docs/topic-format.md` (or fold into README) before retiring. |
| `docs/09-verification.md` | V-* rule IDs are cited by every test and error payload; the registry (`validate/registry.py`) has ids+one-liners but not the rationale prose. | None strictly needed (code+tests carry semantics); recommend keeping ONLY if you want rule rationale prose somewhere. Otherwise retire. |
| `docs/10-v1-design.md` | **Hard test dependency**: `test_template_drift.py::test_docs10_section5_carries_the_template_files_verbatim` byte-syncs docs/10 §5 to the template files; the closed CLI list is mirrored in `test_cli_envelope.py`. | Rework that test to pin the template files alone (they are already the canonical text); CLI surface stays pinned by `CLOSED_COMMANDS`. |
| `docs/11-test-suite.md` | Worklists (T-r3/T-S*/T-v2.1*) were spec-ahead-of-code task lists — all landed; test structure is self-describing. | None; retire after confirming no open worklist item remains (all shipped as of v2.1.1). |
| `docs/12-webui-spec.md` | UI design tokens/a11y/glyph rules are not in code comments; retiring loses design rationale (not correctness). | Retire only if you accept the UI code as its own spec. |
| `CLAUDE.md` (repo instructions) | Points every session at `docs/00`–`18` as the source of truth. | Rewrite to point at `docs/contracts/` + code/tests (I draft it on approval). |

## C. Delete — already superseded, kept only as clutter

| Path | Reason |
|---|---|
| `archive/legacy-2026-07-07/` (80 K) | Explicitly superseded by CLAUDE.md ("never follow it"); git history retains it. |
| `docs/contracts/_legacy-context.md` | The rebuild's compaction scratch file — gitignored, "CONTEXT ONLY", to be thrown away per protocol. |

## Not candidates (stay)

- `src/paperproof/prompts/*.txt` — canonical worker contracts, drift-guarded.
- `tests/**` — the executable spec; rule coverage is measured here.
- `docs/contracts/{architecture,structure,interfaces,deletion-manifest}.md` — the new layer.
- `data/projects/**` — live-run state (ai-jobs-2 checkpoint included).
