# Gate report — m4-surface, attempt 1

## Generator result (Opus/high, fresh)
- `pytest -q`: **375 passed** (367 + 8 new); full gate exit 0 (orchestrator re-ran). No regression (S7/determinism/verify anchors green). 43-command surface unchanged.
- New src: db/{indexer} (rebuild/check/IndexReader), ui/{readmodel,app,static/index.html,static/vendor/cytoscape.min.js}; db+ui CLI groups real; verify adds db-manifest-freshness warning (exit 0).
- New tests: test_api (6), test_s8_rebuild (2); test_cli_envelope updated (no stubs remain).

## Orchestrator action: real cytoscape vendored
- Generator shipped a 4KB cytoscape STUB (no network in its context) — Logic Map would not render. Orchestrator fetched the real cytoscape 3.30.2 (373KB, official unpkg, genuine copyright header) and swapped it into ui/static/vendor/. All 375 tests still green (the static-page test scans index.html for external URLs — unchanged — and just asserts the asset serves 200). Logic Map now functional with the genuine library. No external fetch at runtime (vendored locally).

## Generator OPEN DOC ISSUES → disposition
1. table `verdict_records` (source proof_results.jsonl) — docs/07 lists "verdict_records/proof_results". Accept.
2. uniform hot-column schema (NULL where N/A). Accept.
3. db check hashes bytes, doesn't parse (reports stale on corrupt, parsing readers exit 3). Accept (docs don't require check to parse).
4. Overview "open" = {queued,claimed,running,validating,blocked,stale}. Accept (docs pin the question).

## Evaluator verdict — PASS

Fresh adversarial re-check (own probes under /private/tmp, own monitor fixtures). Every M4 claim independently reproduced; no blocking findings.

### Independently reproduced
1. **Gate / hollow-scan.** `pytest -q` → 375 passed, exit 0, no M0–M3 regression. AST/grep scan of test_api.py (48 asserts) + test_s8_rebuild.py (14 asserts): no `pytest.mark.skip`/`xfail`/`assert True`/`...` — the two "skip" hits are the word inside comments/docstrings, not test logic.
2. **Reads hit the INDEX, not JSONL (the top hollow risk) — PROVED.** Built S7-shaped project, `db rebuild`, recorded `/api/overview` (worker-1→NODE-007). Then appended a hand-written out-of-band record to `queue/work_items.jsonl` flipping that item to queued, WITHOUT rebuild. Endpoint STILL returned the OLD indexed value (worker-1→NODE-007) AND `stale_index=true` (`changed_sources=['queue/work_items.jsonl']`). Repeated GETs did NOT auto-rebuild (stayed stale) — auto-rebuild fires ONLY when `db/` is absent. The stale banner is therefore load-bearing, not decorative.
3. **`db rebuild` idempotent (docs/07 §Derived DB).** Two rebuilds → identical `sources` hashes, identical `tables` row counts, identical table CONTENTS (full history dump diff), and byte-identical `index_manifest.json`. `*_current` returns latest-per-id while base tables keep full history (appended a 2nd version of WI-000001 → base history=7 versions, `_current`=1 row = latest).
4. **S8 corruption → every PARSING reader exits 3 (docs/09 S8, docs/11 §8).** Corrupted line 1 of `graph/logic_nodes.jsonl`. Exit 3 naming `logic_nodes.jsonl:1` from: graph list-nodes, list-edges, show, **msa-check (NOT covered by the shipped S8 test)**, verify, db rebuild, trace, compiler dry-run, freeze apply, queue list, queue events, proof build-tasks, commit apply. No reader swallowed/skipped the line. Legitimate exit-0/non-3: `db check` (hashes bytes by design → reports `stale_index=true`), `project status` + `spec show` (never read graph content — `project status.msa` is hardcoded `None`, snapshot id via byte-hash). WebUI: db-present+corrupt → serves stale index + stale banner; **db-absent+corrupt → CorruptStateError caught by `_guarded` → corruption-lock payload naming file+line** (docs/12 banner priority 1); POST `/api/db/rebuild` over corrupt → `{ok:false, corrupted:true}`.
5. **Six Overview questions from REAL data.** Pristine fixture: open=4 (concrete WI ids), working worker-1→NODE-007 / worker-2→NODE-008 (per-agent claims), blocked=2 (EDGE-007-008-dep, EDGE-008-009-dep), committable=1 (WI-000015, a validated item), frozen=1 (NODE-002), stale_index=false, dead_letters real (S5 dead-letter path independently exercised by the shipped test, mechanism identical), MSA computed from the indexed graph (all_pass=false — a real value, L1 lane incomplete). `/api/record/NODE-002` = canonical latest (active, frozen, 3 history versions, 1 verdict). No hardcoded/empty answers found.
6. **Closed HTTP surface.** Enumerated routes = exactly docs/07: 8 GET (overview, graph, record/{id}, queue, events, evidence, compiler, trace/{node}) + 3 POST (queue/{id}/claim, /release, db/rebuild) + static mount at `/`. No stray, none missing. POST claim/release call `queue_engine.claim/release` — the SAME path `cli/commands.claim` uses (verified: `commands.claim` → `engine.claim`); a UI claim appends a queue event with `actor=<agent>` (event-log parity, docs/12 P1); unknown id → 404.
7. **No external fetch (docs/10 §2).** Only local `vendor/cytoscape.min.js` (real 373KB lib, genuine Cytoscape Consortium header — pre-noted, not re-flagged); zero `http(s)`/`cdn` strings in index.html; `/` and `/vendor/cytoscape.min.js` both 200; 5s `setInterval` polling that pauses on `document.hidden`.

### Judgment on the 4 generator dispositions — all SOUND
1. Table `verdict_records` ← `proof_results.jsonl`: docs/07 line 186 literally names the table `verdict_records` in the closed set. OK.
2. Uniform hot-column schema (id, seq, json + 5 hot cols, NULL where N/A): matches docs/07 "extracted hot columns … as applicable". OK.
3. `db check` hashes-not-parses: docs/07 lines 79–80 define check as a hash comparison, not a parse. I confirmed the split empirically — parsing readers exit 3, check reports stale. Re the point-8 gap: a canonical JSONL corrupted while the index is present is served as stale-but-valid indexed data UNDER the stale banner, escalating to the corruption lock only when a rebuild is attempted. No command serves wrong answers *without* a banner — reads that can't detect corruption (they never parse JSONL) still fly the stale flag, and the first rebuild locks the UI. Consistent with docs/12's "exit-3 semantics" trigger and the derived-index philosophy. Sound.
4. Overview "open" status set: docs pin the question, not the enum; the chosen non-terminal set (validated split out as Q4 "committable") is defensible. OK.

### Non-blocking notes
- N1: `project status` returns `msa: None` hardcoded (docstring says "MSA summary"). Pre-existing pre-M4 code, out of M4 scope; the WebUI `/api/overview` computes MSA correctly from indexed records. Worth a future cleanup.
- N2: Corruption of a canonical JSONL while `db/` is present presents in the UI as the *stale* banner, not the *corruption* banner, until the next rebuild attempt (which then locks it). This is by-design per docs/12's exit-3-semantics trigger, but is a subtle escalation path worth a one-line mention in docs/12 §2 so operators know "stale" can mask "corrupt" until rebuild.
- N3: docs/07 explicitly permits "htmx/vanilla JS"; the impl is vanilla-JS `fetch` + `setInterval` (no htmx library). docs/12 P5/§2 phrasing ("htmx polling") is slightly ahead of the impl; behavior (5s, pauses on hidden tab) matches. Trivial doc drift.
