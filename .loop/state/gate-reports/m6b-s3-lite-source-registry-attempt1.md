# Gate report — m6b-s3-lite-source-registry (attempt 1)

**Result: PASS (worktree build).** `419 passed` (399 baseline + 20), `paperproof
verify` exit 0. Isolated worktree build; a fresh Evaluator grades after merge.

- Branch: `worktree-agent-afa4f7c7442563408`
- HEAD: `555ff18cb96c4caab6771f4fd83abdf5219ffdef`
- Base: `4e5860a` (m5, 399 green) — NOTE the branch base is the pre-adoption m5
  commit, not `967a8cf`; docs/16 arrived here design-frozen, so the adoption
  docs (docs/00 entry, tier table, contract A37–A39) were CREATED as doc-sync.
- Gate: `.venv/bin/python -m pytest -q` from worktree root. A dedicated
  worktree `.venv` was created (`uv venv` + `uv pip install -e ".[dev]"`) because
  the parent repo's shared `.venv` editable-install resolved `paperproof` to the
  parent src (which already contains the merged S1+S3), masking worktree code.

## Scope built (docs/16 Stage A-lite only)
Registry + recipes + provenance. Stage B triangulation (V-SRC-04) NOT built.

## Per-assertion status
- **A37 (schemas)** PASS — `source_profile.v1` (+`tier_note`) and `document.v2`
  (= v1 + `provenance`) registered (`schemas/docs.py`, `schemas/__init__.py:46-48`),
  golden fixtures round-trip; `document.v1` stays registered + readable.
  `test_schemas`, `test_v_src::test_document_v2_roundtrip_and_v1_still_valid`.
- **A38 (learns + provenance)** PASS — `docsdb/registry.py:learn()` upserts a
  SourceProfile per web domain; tier via `TIER_TABLE`; `blocked_direct` via
  `_blocked_texts()` (search_log OR query_log outcome=blocked); ingestor writes
  `DocumentV2` + provenance (`docsdb/ingest.py`); dispatch excerpt via
  `matched_profiles()`/`check_registry_excerpt()` [V-SRC-05]; prompt REGISTRY
  block. `test_v_src` T-S3-1/4, `test_template_drift`.
- **A39 (rules+CLI+storage+tests)** PASS — `validate/rules/v_src.py`
  V-SRC-01/02/03/05 registered (`validate/registry.py`), rule-coverage green;
  `docs source list|set` (`cli/app.py`, `docsdb/commands.py`); `docs/sources.jsonl`
  (`paths.py`, verify sweep `verify.py`); T-S3-1/2/4 + all prior green.

## Doc files amended (doc-sync)
docs/16 (status + explicit source_type→tier table + tier_note + defensive log
learning + fetch_method-direct note + Stage B marked NOT adopted); docs/00
(Search Program Adoption entry); docs/09 §1 (V-SRC family); docs/10 §4 (`docs
source` rows) + §5 (DocsWorker REGISTRY block, synced to shipped prompt); docs/11
§12 (T-S3 worklist); `.loop/state/contract.md` (A37–A39).

## Pre-existing tests migrated (equal strength)
None deleted or weakened. Two additive test edits only:
`test_cli_envelope.py` +`docs source list`/`docs source set` in CLOSED_COMMANDS;
`test_rule_coverage.py` +4 SCENARIO_COVERED entries. No `document.v1` output
migration was needed — no prior test asserts a document's schema_version or bytes,
and the ingestor's switch to document.v2 preserves every v1 field.

## Integration point flagged (merge with S1)
`blocked_direct` is learned from the query/search log. This build reads block
signals DEFENSIVELY from `search_log` strings (docs_result.v1, what this worktree
has) OR `query_log` entries with `outcome="blocked"` (S1's docs_result.v2), so it
merges cleanly once S1's query_log lands. See `registry._blocked_texts`.
