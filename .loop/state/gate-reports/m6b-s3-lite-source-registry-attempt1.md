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

---

## Evaluator verdict

**Result: PASS.** Fresh adversarial grade on main (HEAD `a3bc3a2`) after the S3-lite
merge + S1 + S2 adoption. I assumed the work was broken and could not break it.

### Gate re-run (mandate 1)
- `.venv/bin/python -m pytest -q` → **457 passed, 1 warning**; `-rsxX` shows **0
  skipped / 0 xfail / 0 xpass**. Nothing masked.
- Built a project through the **v2 ingest + registry-learning path** (proof-raised
  DocsRequest → committer wires plan → FakeDocsWorker emits `docs_result.v2`),
  persisted it, and ran the real binary out-of-process:
  `python -m paperproof --root <persisted> --project p4-ldi verify` → `{"ok": true}`,
  **exit 0**. The learned `docs/sources.jsonl` carried `blocked_direct:true`,
  `tier:T4_industry_data` for `fred.stlouisfed.org`.

### Independent adversarial probes (my own inputs, 8/8 passed — scratchpad, not committed)
- **A37 schemas**: `source_profile.v1` + `document.v2` (=v1+provenance) + `document.v1`
  all registered; v2 round-trips; **v1 still parses/validates as v1** and a v1 doc is
  correctly *rejected* by `DocumentV2` (provenance required); `extra="forbid"` proven
  on both `DocumentV2` and `Provenance` (unknown field ⇒ ValidationError).
- **A38 tier learning**: drove `registry.learn` for **all six** source_types →
  correct tier per the fixed table; unknown type → `T6_other`. Every ingested web doc
  is `document.v2` with `provenance.tier ∈ enum`.
- **A38 dispatch excerpt [V-SRC-05]**: constructed T1 `census.gov` + off-topic T3
  `nber.org` + facet-matched **non-T1** `adp.com`; excerpt contains census + adp,
  excludes nber; dropping the facet-matched **non-T1** profile fires V-SRC-05.
- **A38/A39 blocked_direct — the integration seam**: independently drove a 403 on
  `fred.stlouisfed.org`. Proved (1) `blocked_direct=True` learned; (2) the **actual**
  `docs_result.v2` the worker wrote carries the blocked `X1` extra AND `v_sp.check`
  over its immutable plan returns **[]** — the blocked X-id does **not** violate
  V-SP-01/03 (X-ids aren't plan qids; `executed=false`+`outcome=blocked`+non-empty
  note satisfies V-SP-01; `docs_taken(0) ≤ urls_seen(0)` satisfies V-SP-03); (3)
  `registry._blocked_texts` reads **both** `search_log` (v1) and `query_log`
  `outcome=="blocked"` (v2), and yields no signal on clean logs of either shape.
- **A39 V-SRC-01/02/03**: each rule fires by id on a hand-crafted violation
  (tier-out-of-enum & missing provenance sub-field ⇒ V-SRC-01; dangling AND
  no-quoted_via secondary_quote ⇒ V-SRC-02; carrier-present ⇒ clean; silent tier
  change, both **lower and raise**, ⇒ V-SRC-03). `docs source set --tier` refuses a
  silent lowering (exit 1, `V-SRC-03` in errors, **no record appended**) and accepts
  the same change WITH `--note`. Rule-coverage meta-test green.

### Integration-seam fix judgment — LEGITIMATE (not a paper-over)
The FakeDocsWorker change (`tests/fakes/workers.py:160-169`) converts a v1-style
`search_log` block line into a blocked `X{j}` `query_log` entry. This faithfully
mirrors the **real** DocsWorker contract in `prompts/docs_worker.txt`: extra fetches
are logged as `X1/X2…`, and a query that could not run is `executed=false,
outcome=blocked` with a reason note. The learning then flows through **production**
code unchanged (`ingest.ingest_result` → `registry.learn` → `_blocked_texts` reads
`query_log.outcome=="blocked"`), so the seam is exercised end-to-end, not stubbed.
Diff vs `gate/m6-s1-search-planning` is **+12 lines, 0 deletions** — no existing fake
behavior weakened. Without this the v2 path would silently lose the 403 signal S3
needs, so the fix restores a real capability rather than masking a gap.

### Regression / doc-sync
- `tests/` diff vs `gate/m6-s1-search-planning`: **+290 insertions, 0 deletions**;
  vs `gate/m5-r3-behavior`: no removed `def test`/`assert`/`class` lines. Prior V-DR /
  ingest / cascade / cache suites intact. `src` change is additive (617 ins / 13 del;
  the 13 are the `Document`→`DocumentV2` swap + `v_src` registration — all v1 fields
  preserved).
- Re-derived **V-SRC-01** and **V-SRC-03** from docs/16 §Rules — code matches
  (V-SRC-01 v1-exempt is legitimate: the ingestor now writes v2 on every path, so
  the exemption only covers pre-registry legacy records; V-SRC-03 enforced
  symmetrically on any noteless tier change, consistent with docs/09 wording).
- **V-SRC-04 absent**: not in `validate/registry.py`, not defined in `v_src.py`, no
  triangulation code; docs/00 + docs/16 + docs/09 all mark Stage B NOT ADOPTED.
- docs/16 tier table == `registry.TIER_TABLE`; `docs/sources.jsonl` created by init
  (`paths.py:53`) and schema-swept by `verify` (`verify.py:31,118`). No CLI/schema
  surface beyond `docs source list|set` + the two schemas.

### Non-blocking observations (not defects)
- `blocked_direct` learning is domain-substring matching on the log note: a real
  worker's block note that omits the domain string would miss the signal. This is
  identical on the v1 and v2 paths and pre-dates this change (a 403 note realistically
  carries the URL), so it is a documented design property, not a regression.

No defect found. Gate stays PASS.
