# Gate report — m0-foundation, attempt 1

## Generator result (Opus/high)
- `uv pip install -e ".[dev]"`: clean.
- `.venv/bin/python -m pytest -q`: **171 passed in 0.43s**.
- Full gate command (pytest + 8 file-presence): **GATE_EXIT=0** (independently re-run by orchestrator, confirmed).
- Cross-root byte-determinism verified; docs/ untouched by generator.

### Test counts (171)
schemas 70 · cli_envelope 49 · v_path 15 · textutil 13 · v_spec 8 · ids 6 · jsonl_store 6 · snapshot 4.
23 schemas round-tripped; 43-command closed surface asserted both directions; P4 golden byte-exact.

### Open doc issues raised by generator + orchestrator disposition
1. Stopword count "72" vs 82 listed → **DOC FIXED** by orchestrator (docs/09 §0 → "82 words"); code (verbatim 82) is correct.
2. created_at on docs_request/compiler_dry_run/draft_map/audit_report → code follows docs/07 convention ("convention wins"); **no doc change**, code correct.
3. V-SPEC-03 unreachable from pure topic file → fixture uses a paper_spec merge-patch to inject a cycle. Reasonable; **accept**.
4. V-SPEC-04 co-trips V-SPEC-01 → fixture asserts V-SPEC-04 ∈ failed_rules (docs/11 §4 permits co-trip). **Accept**.
5. V-PATH-04 = prefix rule + no-stray-writes scan (reconciles H10 mapping). **Accept** (matches docs/05 + docs/11 §6).
6. Fixtures: topics/ for V-SPEC, vrules/ for V-PATH (docs/11 §4 authoritative). **Accept**.
7. project init creates db/ dir only (index is M4-derived). **Accept**.
8. spec accept non-interactive (running it = confirmation). **Accept** (docs/10 §4).

### Generator flagged for evaluator scrutiny
- CLI envelope under vendored typer click (exit-code classification by MRO name; standalone_mode=False).
- Canonical determinism via @model_serializer omitting absent keys (partial Scope, NODE vs EDGE forms).
- Byte-exact golden P4 derivation (structured scope vs verbatim in_scope; en-dash/CJK UTF-8; --patch order).
- safe_resolve symlink/traversal (resolve()-based; TOCTOU).

## Evaluator verdict
(pending — fresh adversarial subagent)

## Evaluator verdict — PASS

Fresh adversarial review (did not write this code). Gate re-run: `171 passed` under
`.venv/bin/python -m pytest -q -p no:cacheprovider`, exit 0. Per-file counts match the
self-report (schemas 70 · cli 49 · v_path 15 · textutil 13 · v_spec 8 · ids 6 · jsonl 6 ·
snapshot 4 = 171). The suite is NOT hollow: no `xfail`/`skip`/`assert True`; the only two
functions an AST scan flagged as assertion-free (`test_symlink_escape_rejected`,
`test_unknown_field_rejected`) both use `pytest.raises`, i.e. genuine assertions.

Independently verified (not "looks good"):

1. **textutil (§0) — attacked in a REPL, no divergence from the literal spec.** CJK `is_cjk`
   ranges correct (中 Han, 㐀 Ext-A, あ/ア kana, 한 Hangul true; a/1/é/々 false). `sentence_split`:
   ASCII `.!?` split only before whitespace/EOL (`a.b`→1, `3.14 is pi`→1); CJK `。！？` split
   ALWAYS incl. the P4 `重构。以下` case (→`['重构。','以下']`) and `a。b`→2. `word_count`
   mixed CJK/ASCII (你好 world → 3). `quote_match` normalizes whitespace, preserves case
   (`The Quick`/`quick`→False). `scope_compatible` year-range intersection, region casefold,
   actors/mechanisms intersection, missing-keys-never-conflict all correct. `STOPWORDS` len == 82.
2. **Three rules re-derived + fixtures audited.** V-SPEC-01 fixture genuinely omits the
   Success Criteria section (isolated V-SPEC-01). V-SPEC-05 fixture has exactly 2 seeds
   (isolated); I also proved the untested `≤2 sentences` branch fires on a 3-sentence ASCII
   seed AND a 3-sentence CJK seed, and passes a 2-sentence seed. V-PATH-02 traversal/symlink
   fixtures + hand test both fire the named rule; pass fixtures don't. No fixture found that
   trips a different rule but is asserted against this one. (V-SPEC-04 co-trips V-SPEC-01 by
   also dropping the Exclusions heading, but it genuinely violates V-SPEC-04 and docs/11 §4
   permits incidental co-trips.)
3. **CLI closed surface + envelope.** Enumerated the typer tree: exactly the 43 docs/10 §4
   commands, no drift either direction. Real-subprocess attack via the `paperproof` console
   script: stub→exit1 single `NOT-IMPLEMENTED` envelope; missing-arg→exit2; unknown command
   →exit2; no-args→exit2; success→exit0; domain fail→exit1 — each exactly one JSON envelope
   `{ok,command,data,errors,warnings}` on stdout, stderr clean. Could not force two envelopes,
   non-JSON, or a wrong exit code on any of the 43 commands.
4. **Byte-exact golden (A3) re-derived from docs/01, not trusted.** Golden PaperSpec/Contract
   match the documented derivation: structured scope from P6; `in_scope` = verbatim Scope list
   items (incl. `Period:` prefix); `forbidden_claims` = Exclusions; `out_of_scope` = []; en-dash
   `–`, em-dash `—`, arrow `→` and CJK all preserved; `--patch` order proven (spec-level
   core_question propagates into contract.fixed_question; contract-level patch wins last; a
   merge-patch `null` deletes a Scope key and it is omitted from output, not emitted as null).
   A fresh `spec build` reproduces the golden byte-for-byte, so the golden is not stale. The
   test fixture `topics/ok_p4.md` is identical to `examples/topic-input-p4.md`.
5. **Schemas (A2).** Independently injected an unknown top-level field into all 23 golden
   fixtures → every one raises ValidationError (extra="forbid" real); nested Scope also rejects
   unknowns; paper_type enum enforced; all 23 round-trip to a fixed point. Registry keys ==
   exactly the 23 `*.v1` tokens that appear anywhere in docs/ (diff empty). None missing.
6. **Store (A5).** safe_resolve rejects dir-symlink escape (existing AND non-existent leaf),
   file-symlink escape, nested-under-symlink, relative `../` symlink, absolute paths, and
   mid-path `..`; allows legit inside paths and symlink-to-inside. Append-only keeps full
   history (3 physical lines after re-writing id X), latest_by_id returns the newest version.
7. **Determinism (docs/11 §3).** `spec build` into two independent roots under the same
   PAPERPROOF_NOW → byte-identical paper_spec.json and project_contract.json.

Non-blocking observations (none gate-failing):
- `src/paperproof/textutil.py:14` comment still reads "Exactly 72 words" while the actual
  frozenset (and the doc, and test_textutil.py) are 82. Stale comment only; the list is correct.
- Under `python -m paperproof` (not the product path), the error-envelope `command` label is
  polluted to e.g. `-m paperproof spec build`; under the real `paperproof` console script (what
  docs/10 §8 demo uses) it is clean (`spec build` / `unknown`). Cosmetic; no test asserts the
  polluted value.
- `paperproof --help` / `-h` print human help text and exit 0 instead of a JSON envelope.
  `--help` is not one of the 43 commands, so this does not violate the closed-surface contract,
  but the "every command prints one JSON object" statement is absolute — worth a doc note.
- Golden `scope.period` = "2020–2023, centered on September–October 2022" is a faithful verbatim
  P6 copy, but is not a parseable year range, so downstream `scope_compatible` (V-NODE-03) will
  silently fall back to substring matching in M1+. Consistent with the documented derivation;
  flagging for M1 awareness only.

Only PASS closes this gate. Verdict: **PASS**.
