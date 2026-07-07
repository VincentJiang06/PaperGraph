# Gate report — final-audit (recreated after a subagent deleted the original)

## Fresh-clone gate (A25) — orchestrator run
- Used the 3.12-pinned form (contract.md env note; design's bare `python3 -m venv` would grab system 3.9).
- **First run FAILED**: `ModuleNotFoundError: No module named 'paperproof.db'`. Root cause: `.gitignore` bare `db/` (for the per-project derived index under data/) ALSO matched src/paperproof/db/, so the whole M4 db package was never committed. Dev checkout had it on disk (377 green locally); every fresh clone was broken. No earlier gate could catch it — only the fresh-clone gate.
- Fixed: ignore scoped to `data/**/db/`; committed the swallowed db/__init__.py + db/indexer.py.
- **Re-run PASSES**: fresh clone, clean 3.12 venv, `paperproof.db` imports OK, **377 passed, exit 0**.

## Final-audit verdict — PASS (by the final-audit evaluator, independently reproduced)
Automated definition-of-done met. A26 live smoke (real Claude workers) remains human-only.

Independently reproduced by the evaluator:
- Fresh-clone gate: 377 passed exit 0 FROM THE CLONE; paperproof.db/ui/prompts/ui-static all present; no absolute paths.
- Global invariant sweep on a real S7 project: verify exit 0 (schema+graph+V-PR-12+queue+commit+crossref+db-freshness); corrupt one stored verdict → exit 3 (V-PR-12).
- rule_coverage real: 50 registry rules each fixtured/SCENARIO_COVERED; deleting vrules/V-PR-14/ makes the meta-test FAIL naming it.
- Weakened-test hunt across gate/m0→m4→HEAD: CLEAN (no deletion/weakening/skip; stub list shrinks legitimately, M4 broadens to full CLOSED_COMMANDS).
- Sampled rules (V-PR-14, V-DR-05, V-FRZ-04, V-CDR-01) faithful to docs/09.
- CLI surface == docs/10 §4 closed list; S1–S8 substantive.

Low, non-blocking findings (surfaced by the final audit + two corroborating sub-audits):
1. commit_queue ordering sorted by work_item_id vs docs/05 "FIFO by validation time" → CLOSED in polish (sort by (updated_at, work_item_id)).
2. `uv build --wheel` failed (force-include collided with packaged prompts) → CLOSED in polish (artifacts for ui/static; prompts ship as package data; wheel verified).
3. trace claim-annotation regex stricter than writers → CLOSED in polish (same \(claim:\s*id\s*\) regex).
4. text_path non-null for text-less ingest-result docs vs docs/04 → CLOSED in polish (null when no text).

Recorded residue (tracked, not defects affecting any shipped scenario; for a future hardening pass):
- rule_coverage guards only the ~50 boundary rules in registry.RULES; the V-GATE/V-NODE/V-GRAPH/V-FRZ/V-CDR/V-PROSE/V-AUD families have dedicated test files but aren't in the coverage completeness net. HARDEN-NEXT #1.
- sha256("") dedup collision for (degenerate) text-less web docs; audit applies forbidden-language union across sections (harmless superset); section_plan has no alternative-type bucket (unreachable normally).

## Status: automated DoD MET. Remaining human node: A26 live smoke (real workers), A27 doc-first spot-audit (evaluator found only finding #1 as an un-paired doc divergence, now reconciled by fixing code→doc).
