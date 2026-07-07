# Gate report — m2-docs, attempt 1

## Generator result (Opus/high, fresh)
- `.venv/bin/python -m pytest -q`: **335 passed** (312 M0+M1 + 23 M2); full gate exit 0 (orchestrator re-ran, confirmed). No regression (decision table / v_commit / determinism subset green).
- New src: docsdb/{matcher,pack,cache,ingest,commands}, validate/rules/v_dr.py; committer needs_docs wiring; prooftask matcher-populated DocsPack; docs CLI group real.
- New tests: test_v_dr (D01–D05 + quote_match), test_docsdb, S2 (cache + born-dead), S3 (contradiction cascade), FakeDocsWorker.

## Generator OPEN DOC ISSUES → disposition
1. S2 cap vs pass on one target: split across NODE_A (happy+cache) and NODE_B (cap) in one project. Reasonable; accept.
2. docs build-pack vs -rN immutability: standalone build-pack writes the task's declared docs_pack path; pipeline mints -rN via build-tasks. Accept (both commands real).
3. docs ingest-result item terminality: validating→validated→committed (2 events, mirrors ingest-prose). Accept (existing rule).

## Evaluator verdict — PASS

Fresh adversarial review. Assumed broken; every claim below was independently reproduced with my own throwaway probes under /private/tmp (not the generator's tests). Full suite re-run: **335 passed, exit 0**; M2-only subset 23 passed.

### Independently reproduced
1. **Hollow-scan (AST) of the 4 new test files** — test_v_dr (15 cases via 12 parametrized fixtures + 3), test_docsdb (6), test_s2_docs_loop, test_s3_contradiction: zero trivial `assert True`/`assert 1`, zero skip/xfail, zero zero-assertion tests. S2 carries 18 asserts, S3 carries 9 — all substantive. No M0/M1 regression: test_rule_coverage.py is dynamic over `registry.rule_ids()` (only a docstring changed); apply.py/builder.py edits keep all M1 scenarios green.
2. **Cache hit creates NO work item (A17)** — drove NODE→needs_docs→ingest, then re-issued the identical need+hints. By my own count of distinct docs_queue items in the raw `queue/work_items.jsonl`, the count did **not** increase; the DocsRequest is `status=fulfilled, fulfilled_by="cache"`, `work_item_id=None`. A **non-matching** request (different need+hints, unrelated target claim) correctly **misses** (status=open + a new docs_queue item). No wrong-claim leak is reachable: the cache only skips dispatch/unblocks the re-proof; citations always flow through the claim-scoped matcher at `-rN` pack-build, never straight from the cache.
3. **Matcher (docs/04)** — score = |tokens(claim) ∩ (tokens(summary)∪tokens(quote)∪tokens(join(can_cite_for)))| exactly (verified in source + by probe). A score-1 overlap is EXCLUDED; a score≥2 EU with incompatible scope (region UK vs US) is EXCLUDED, and included when compatible. Order is (score desc, evidence_id asc) — a tie resolves by evidence_id asc, identical across two runs.
4. **quote_match anti-fabrication (A16/V-DR-05)** — through the FULL ingest path: a kind=quote EU whose text is not a whitespace-normalized substring is REJECTED with V-DR-05 and **nothing is archived** (0 EUs, 0 docs). A genuine quote with different whitespace/newlines is ACCEPTED. kind=paraphrase with a non-substring string is NOT subjected to the check (accepted, archived). Also verified V-DR-05 fires on the `doc_id`→archived_texts path, not just `doc_ref`.
5. **content_hash dedup (docs/04)** — same file bytes twice via `docs ingest` ⇒ one Document, same doc_id, no second record. A DocsResult web doc whose inline text is byte-identical to an existing doc dedups by content_hash (no new document; EU repoints to the pre-existing doc_id). citation_key collisions append -b then **-c** (third collision verified).
6. **Born-dead cap = 2 (A17)** — drove NODE-003 through 2 completed **not_found** cycles, then a 3rd needs_docs: the re-proof item is BORN dead ((created)→dead, op=dead_letter in `queue/events.jsonl` with from_status null) and **no third DocsRequest** is appended (distinct request_id count stays 2). Confirmed the counter counts COMPLETED (fulfilled/not_found) cycles only: an open miss yields `_docs_completed_cycles==0` and does not prematurely dead-letter. `verify` exits 0 over this state (a not_found DRES resolves solely via `fulfilled_by`).
7. **S3 cascade completeness (A18)** — contradicted fact → rejected(contradicted) + tombstone(contradicted); EVERY incident edge → rejected(endpoint_rejected) + tombstone(endpoint_rejected); no open (queued/blocked) items remain for those edges and a `cancel` op is present in the event log. The contradicting verdict's evidence (EU-001) is genuinely served: I independently ran `pack.assemble` on the re-proof target and got a non-empty matcher pack containing EU-001 with matching documents_meta — not a stub. `verify` exits 0 (it truly recomputes verdicts via V-PR-12 and replays every CommitDecision via V-COMMIT-04, not a no-op).
8. **V-DR discrimination** — all 6 rules registered, each with ≥1 pass_ and ≥1 fail_ fixture; D01→V-DR-02, D02→V-DR-05, D03→V-DR-03, D04→V-DR-01, D05→V-DR-06 mappings hold. Novel hostiles the catalog omits also caught: doc_ref out of range → V-DR-01, doc_id-not-archived → V-DR-01.

### Judgment on the 3 generator dispositions
1. S2 cap-vs-pass split across NODE_A (happy+cache) / NODE_B (cap): sound — the cap is per-target (`target_id`-scoped counter), so one project legitimately exercises both. Accept.
2. build-pack vs -rN immutability: confirmed. `build_bundle` mints a fresh `DOCSPACK-<target>-rN.json` per revision via the matcher; the standalone `docs build-pack` writes the task's declared path. Packs are immutable per revision. Accept.
3. ingest-result terminality (validating→validated→committed, 2 events): confirmed in ingest.py (validate_pass then commit_item), which unblocks the waiting re-proof. Accept.

### Non-blocking observations (not gate-blocking)
- `_cancel_open_items` (cascade) cancels items in {queued, blocked, stale, failed} but not a mid-flight claimed/running/validated item. In S3 the incident-edge item is `blocked`, so it is cancelled; a cascade landing while an incident edge is actively being proved would leave that in-flight item uncancelled (it would later fail V-COMMIT on a rejected endpoint). Acceptable for v1; worth a note if concurrency semantics tighten.
- The request fingerprint uses `.lower()` (docs/04's own normalize) while the matcher tokenizer uses casefold (docs/09 §0). Each matches its own spec section; not a defect.
