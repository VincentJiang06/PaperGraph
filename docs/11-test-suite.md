# 11 Test Suite

The executable test plan. `docs/09` says *what* is verified (rules, matrix, scenarios); this doc says exactly *how*: runner, layout, fixtures, fakes, meta-tests, and the per-milestone gates. On any question about test structure, this doc is authoritative.

Two design commitments:

```text
1. No LLM in the suite. Everything is deterministic; real workers appear only
   in milestone live-smoke, outside pytest's default run.
2. Coverage is measured in RULES, not lines: every V-* rule id must be provably
   exercised (meta-test §7), and every decision-table row has a golden form.
```

## 1. Runner and Invocation

pytest, driven in-process. CLI behavior is tested through `typer.testing.CliRunner` (fast, importable), plus a handful of true-subprocess smoke tests for the envelope/exit-code contract.

```toml
# pyproject.toml (test-relevant part)
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-m 'not live'"
markers = [
  "unit: pure-function tests",
  "contract: single-module boundary tests",
  "integration: multi-module scenario tests (S1–S8)",
  "live: real Claude workers — milestone acceptance only, never CI/default",
  "slow: concurrency/fuzz tests (>5s)",
]
```

```bash
pytest                      # everything except live — must be green to merge
pytest -m "not slow"        # quick loop while developing
pytest tests/integration    # scenarios only
pytest -m live              # milestone smoke ONLY, run by the Orchestrator
```

## 2. Directory Layout

```text
tests/
  conftest.py               fixtures: project factory, clock, runner, canonical
  unit/
    test_textutil.py        every §0 algorithm incl. CJK cases
    test_jsonl_store.py     append-only, latest-by-id, locking, traversal
    test_snapshot.py        take/verify/current
    test_ids.py             allocation, widths, EDGE -vN reuse, PT -rN revisions
    test_decision_table.py  24 golden rows + precedence + totality fuzz [slow]
  contract/
    test_schemas.py         registry round-trip + unknown-field/enum rejection
    test_v_spec.py          scoping: golden build + per-rule failing topic files
    test_v_path.py          path safety + post-run scan
    test_v_node_edge.py     graph-record rules (commit-time)
    test_v_exp.py           expansion rules incl. layer-0 and closing proposals
    test_v_task.py          bundle content, staleness, revisions
    test_v_pr.py            THE big one: pass+fail fixture per V-PR rule
    test_v_dr.py            docs results incl. quote_match
    test_v_commit.py        snapshot/frozen refusal, replay equality, cascade
    test_v_q.py             transition table, leases, events, blocked/unblock
    test_v_frz.py           freeze preconditions, union, unfreeze re-open
    test_v_cdr.py           gap kinds, idempotency, auto-cancel, section plan
    test_v_prose_aud.py     annotation grammar, audit finding kinds
    test_cli_envelope.py    CLI conformance meta-test (§7) + subprocess smoke
    test_rule_coverage.py   rule-coverage meta-test + SCENARIO_COVERED map (§7)
    test_verify.py          verify crossref + snapshot-EOF (H10 remap, T-r3-2)
    test_r3_core.py         r3 core-bug regressions (cache chaining, pack
                            composition, verdict-based cap, evidence-arrival
                            staleness — the live run's four basic failures)
    test_project_status.py  project status carries the real MSA summary
    test_polish_guards.py   final-audit low findings (commit_queue order, wheel
                            package data, trace regex, text_path null)
  integration/
    test_s1_seed_loop.py … test_s8_rebuild.py     (one file per scenario)
    test_determinism.py     same scenario twice ⇒ byte-identical canonical state
  fakes/
    workers.py              FakeProofWorker / FakeDocsWorker / FakeCompileWorker
    scripts/                per-scenario worker scripts (JSON)
  fixtures/
    schemas/                one golden example per schema_version
    topics/                 topic-input-ok.md + broken variants per V-SPEC rule
    forms/                  the 24 decision-table golden forms (N01–N10, E01–E14)
    vrules/<RULE-ID>/       pass_*.json / fail_*.json per validator rule
    hostile/                the hostile worker outputs (§6)
    corpus/                 two tiny .txt "sources" + one tiny .pdf for ingest
    prose/                  valid + violating section drafts
```

## 3. Determinism Harness

Everything canonical must be reproducible byte-for-byte. Three injection points, all environment-driven so the CLI needs no test-only flags:

```text
PAPERPROOF_NOW    RFC3339 timestamp; every created_at/validated_at reads it.
                  The `clock` fixture sets it and provides tick(seconds=1) —
                  monotonically bumping so event ordering stays meaningful.
PAPERPROOF_ACTOR  actor recorded in events/commits (fixture sets "test").
Id allocation     already deterministic (max+1 scan, docs/07) — no injection.
```

`conftest.py` fixtures (signatures are the contract; implementations follow them):

```python
@pytest.fixture
def clock(monkeypatch): ...        # sets PAPERPROOF_NOW, returns .tick()

@pytest.fixture
def pp(tmp_path, clock): ...       # CliRunner wrapper: pp("queue", "claim", ...)
                                   # -> parsed envelope; asserts declared exit code:
                                   # pp(..., expect=1) for expected failures

@pytest.fixture
def project(pp): ...               # init p4-ldi + spec build examples/topic-input-p4.md
                                   # + spec accept; returns the project root Path

def canonical(path) -> bytes: ...  # helper: read file for byte comparison
```

`test_determinism.py`: run S1 end-to-end in two fresh tmp roots with identical PAPERPROOF_NOW sequence ⇒ every canonical file under `graph/ proof/ queue/ commit/` is byte-identical between the two runs. This single test enforces the canonical-serialization convention (docs/07) across the whole pipeline.

## 4. Fixture Catalog

Naming convention is load-bearing (the rule-coverage meta-test globs it):

```text
fixtures/vrules/V-PR-07/pass_bridge_two.json      minimal artifact that PASSES the rule
fixtures/vrules/V-PR-07/fail_three_bridges.json   minimal artifact violating EXACTLY it
```

A `fail_*` fixture may trip other rules incidentally; the test asserts its named rule ∈ `failed_rules`. A `pass_*` fixture must produce `failed_rules` not containing the rule. Topic-file fixtures follow `fixtures/topics/fail_V-SPEC-03_cyclic_bfs.md` etc.

Every schema in the registry has exactly one golden example in `fixtures/schemas/` (used by round-trip tests and as the copy-paste seed for new fixtures).

## 5. FakeWorkers

Table-driven stand-ins with the exact I/O shape of real workers — they read a real bundle and write a real output file, so the whole pipeline path (claim → write → complete → validate → commit) is exercised unchanged.

```python
class FakeProofWorker:
    """mode: 'script' (default) | 'crash' | 'hostile'."""
    def __init__(self, script: dict | Path, mode: str = "script"): ...
    def run(self, work_item: dict, project_root: Path) -> None:
        # reads bundle paths from work_item, renders the scripted form into
        # a schema-valid proof_result.v1 at the DECLARED output path.
        # crash: claims happened upstream; run() returns without writing.
        # hostile: copies a fixtures/hostile/* payload (or performs the
        #          scripted misbehavior, e.g. extra file writes) verbatim.
```

Script format (JSON, lives in `tests/fakes/scripts/`): keyed by target id so one script drives a whole scenario:

```json
{
  "EDGE-001-002": {"form": {"scope_check": "in_scope", "…": "…"},
                    "repair_proposals": [{"kind": "bridge", "claim": "…", "node_type": "definition"}]},
  "NODE-003":     {"form": {"…": "…"}, "language_limits": {"allowed": ["…"], "forbidden": ["…"]}}
}
```

`FakeDocsWorker` (scripted DocsResults, incl. `not_found`) and `FakeCompileWorker` (scripted section prose) follow the same shape. Integration tests drive them via a tiny dispatcher: `drain(queue_name, worker, parallel=N)` claims/runs/completes/validates until the queue is quiet — with `parallel=N` using threads to exercise the locks (S4).

## 6. Golden Decision-Table Forms

The 24 reachable rows. Every one is a fixture in `fixtures/forms/` and a case in `test_decision_table.py`; ids are stable (tests and docs cite them). `n/a` = field absent (NODE) — `n/e` = not_evaluated.

| id | type | scope | dup | wellformed | evidence | inference | assumptions | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N01 | NODE | out_of_scope | f | n/e | n/e | n/a | [] | rejected(out_of_scope) |
| N02 | NODE | in | t | n/e | n/e | n/a | [] | rejected(duplicate) |
| N03 | NODE | in | f | too_broad | n/e | n/a | [] | needs_repair(narrow) |
| N04 | NODE | in | f | compound | n/e | n/a | [] | needs_repair(narrow) |
| N05 | NODE | in | f | single | contradicting | n/a | [] | rejected(contradicted) |
| N06 | NODE | in | f | single | insufficient | n/a | [] | needs_docs |
| N07 | NODE | in | f | single | sufficient | n/a | [] | pass(strong) |
| N08 | NODE | in | f | single | sufficient | n/a | [a] | pass(conditional) |
| N09 | NODE | in | f | single | not_required | n/a | [] | pass(strong) |
| N10 | NODE | in | f | single | not_required | n/a | [a] | pass(conditional) |
| E01–E06 | EDGE | — same six pre-inference rows as N01–N06 with inference n/e — | | | | | | |
| E07 | EDGE | in | f | single | not_required | fails | [] | rejected(contradicted) |
| E08 | EDGE | in | f | single | not_required | gap | [] | needs_repair(bridge) |
| E09 | EDGE | in | f | single | not_required | holds | [] | pass(strong) |
| E10 | EDGE | in | f | single | not_required | holds_w_assum | [a] | pass(conditional) |
| E11 | EDGE | in | f | single | sufficient | holds | [] | pass(strong) |
| E12 | EDGE | in | f | single | sufficient | holds_w_assum | [a] | pass(conditional) |
| E13 | EDGE | in | f | single | sufficient | fails | [] | rejected(contradicted) |
| E14 | EDGE | in | f | single | sufficient | gap | [] | needs_repair(bridge) |

Totality fuzz (`slow`): iterate the full enum product for both task types; every combination either (a) is ladder-valid and computes exactly one verdict, or (b) violates V-PR-14/15/05 and is rejected with that rule id. No third outcome, no exception paths.

### Hostile catalog

Each hostile output is caught by a **named** rule; the mapping is asserted (`failed_rules` must contain it). Validator check order is part of the contract: V-PATH first, then a raw-JSON-tree scan *before* schema parsing — any numeric value anywhere, any key named `verdict`, or any id-valued field outside the schema's own (`task_id`, `target_id`, `duplicate_of`, evidence/docs id lists) ⇒ V-PR-03 — then schema (V-PR-01), then semantic rules. So V-PR-03 is reachable even though schemas are strict.

| id | behavior | rule |
| --- | --- | --- |
| H01 | writes a second file outside allowed paths | V-PATH-04 |
| H02 | correct JSON at wrong output path | V-PATH-01 |
| H03 | invalid JSON bytes | V-PATH-03 |
| H04 | includes a `"verdict"` field | V-PR-03 |
| H05 | 3 bridge proposals on gap | V-PR-07 |
| H06 | cites an EU absent from DocsPack | V-PR-06 |
| H07 | adds `"confidence": 0.9` | V-PR-03 |
| H08 | fact node answers evidence not_required | V-PR-05 |
| H09 | task_id of a different work item | V-PR-02 |
| H10 | appends a line to graph/logic_nodes.jsonl | (r3) caught by `verify`, not the lease scan: the appended record is attributable to no CommitDecision ⇒ V-COMMIT-04 replay mismatch, exit 3. The scan no longer inspects appends — that's what let legitimate concurrent commits break every live validation |
| H11 | out_of_scope but evidence_check answered | V-PR-14 |
| H12 | too_broad without narrow repair | V-PR-07 |
| H13 | would-pass form, language_limits null | V-PR-13 |
| H14 | edge holds + non-empty assumptions | V-PR-15 |
| H15 | duplicate_of id not in ContextPack | V-PR-08 |
| H16 | 200-word notes | V-PR-10 |
| H17 | bridge proposing node_type=thesis | V-PR-09 |
| H18 | inference_check on a NODE_CHECK | V-PR-04 |
| D01 | evidence unit without cannot_cite_for | V-DR-02 |
| D02 | quote not present in archived text | V-DR-05 |
| D03 | evidence unit with a `"strength"` field | V-DR-03 |
| D04 | both doc_ref and doc_id set | V-DR-01 |
| D05 | not_found=true with documents present | V-DR-06 |
| C01 | claims lease, writes nothing, exits | (expiry path, V-Q-05) |

## 7. Meta-Tests (the suite audits itself)

```text
Rule coverage     For every rule id in validate/registry.py: either
                  fixtures/vrules/<id>/ contains ≥1 pass_* and ≥1 fail_* file,
                  or the id appears in SCENARIO_COVERED — a closed map in
                  tests/contract/test_rule_coverage.py from rule id → the
                  integration test that exercises it (e.g. V-COMMIT-01 → S6).
                  An id in neither place fails the build. So does a fixture
                  directory for a rule id that no longer exists.
CLI conformance   The closed command list (docs/10 §4) is mirrored as a constant;
                  the test asserts the typer app exposes exactly that set (no
                  drift either direction), and every command emits exactly one
                  JSON envelope with keys {ok, command, data, errors, warnings}
                  — including on failure (exit 1) and usage error (exit 2).
                  To keep this green from M0: the FULL closed surface is
                  registered in M0, unbuilt commands as stubs returning
                  {ok:false, errors:["NOT-IMPLEMENTED"]} with exit 1; each
                  milestone replaces its stubs with real behavior.
Schema round-trip For every schema_version in the registry: golden example
                  parses; dump→parse→dump is a fixed point; adding an unknown
                  field rejects; each enum field rejects an out-of-enum value.
Decision totality §6. Also: recomputing verdicts over every verdict record in a
                  finished S7 project yields zero mismatches (V-PR-12 at rest).
```

## 8. Integration Scenarios

One file per scenario from docs/09 §3; each ends with `pp("verify")` clean. Key per-scenario assertions beyond the happy path:

```text
S1  bridge candidates carry origin.kind=bridge with the source node's lane+
    layer AND wired edges C→B, D→B exist (docs/08 B6 wiring); the edge re-proof
    item is blocked_by all four bridge items (2 node + 2 edge checks); the
    re-proof ContextPack contains C,D as neighbors of B; final edge strength=
    conditional with the scripted assumptions stored on the record; C,D are in
    the spine afterwards.
S2  after ingest, the DocsRequest fingerprint of an identical need resolves
    fulfilled_by="cache" with NO docs work item created — and (r3) only a
    DRES-fulfilled request is a cache source (a "cache"-fulfilled one never
    chains); the EU is served in the rebuilt DocsPack (-r2) UNCONDITIONALLY
    (REQUESTED composition, V-TASK-05) and the pending re-proof was marked
    stale by evidence arrival (V-TASK-04), no manual build-task; the docs cap
    (r3) fires on the 3rd needs_docs VERDICT with no new evidence since the
    2nd ⇒ re-proof born dead — and an Orchestrator `docs request` between
    verdicts does NOT advance the counter.
S3  cascade: tombstones carry reason=endpoint_rejected; cancelled items emit
    op=cancel events; verify clean. (Runs at M2 — the contradicted verdict
    requires evidence_used from a non-empty DocsPack.) M3 coda: the fixture's
    contradicted fact is the thesis's only support chain, so msa-check fails
    on MSA-9 (vacuous spine) — the item that detects an argument hollowed
    out by cascade.
S4  run with parallel=4 over 8 items: no lost updates (all 8 committed),
    V-Q-02 holds (no double leases in events), events replay to final state.
S5  clock.tick(901) expires the lease; attempt increments; after 3 expiries
    the item is dead and appears in `queue list --status dead` (the
    /api/overview surfacing is asserted by M4's endpoint tests).
S6  the stale item's old bundle files still exist (immutability); the rebuilt
    -r2 bundle reflects the new claim text; verdict record cites -r2 paths.
S7  drives the P4 example to audited prose with scripted workers; asserts
    msa-check items MSA-1..9 individually; asserts the post-freeze dry run
    reports zero gaps (docs/06 reachability note — the gap path is covered by
    V-CDR fixture tests, not S7); trace resolves for every spine node; audit
    passed=true; a seeded forbidden-language sentence in a variant prose
    fixture flips audit to failed with kind=strength.
S8  db rebuild twice ⇒ identical index_manifest hashes; corrupt line N of
    logic_nodes.jsonl ⇒ every CLI command exits 3 naming file+line.
```

## 9. Milestone Gates

The suite is cumulative — a milestone's gate is "**everything green** through its row plus its live smoke". `pytest` (default markers) is the gate command for every milestone; the rows list what must newly exist and pass.

| milestone | new tests that must pass | live smoke (manual, `-m live` + Orchestrator) |
| --- | --- | --- |
| M0 foundation | unit/* (textutil, store, snapshot, ids), contract/test_schemas, test_v_spec, test_v_path, CLI envelope (full stub surface) | none |
| M1 proof loop | test_decision_table (all 24 + fuzz), test_v_pr (full fixture set), test_v_exp, test_v_task, test_v_q, test_v_commit, S1 (through re-proof pass + verify; the freeze coda joins at M3), S4, S5 (dead letter asserted via `queue list`, not the API), S6, test_determinism | one real ProofWorker on the seed edge submits a ladder-valid form computing to needs_repair(bridge); bridges + wired edges appear |
| M2 docs | test_v_dr, docs ingest/dedup/cache tests, S2, S3 (its contradicted verdict needs a non-empty DocsPack, hence the M2 slot; its msa assertion joins at M3) | one real DocsWorker archives a BoE source; identical re-request cache-hits |
| M3 endgame | test_v_frz, test_v_cdr, test_v_prose_aud, S7, trace assertions, S1 freeze coda + S3 msa-check coda | real workers end-to-end on P4 → audited prose |
| M4 surface | S8, db idempotency, /api endpoint tests (FastAPI TestClient) incl. S5's dead letter in /api/overview, UI answers the six Overview questions | UI watched during an M3-style run |

Live-smoke results are recorded by the Orchestrator as a short checklist in `agent_notes/milestones/<M>.md` (pass/fail per item + the ids involved); they gate milestone acceptance but never block `pytest`.

## 10. r3 Revision Worklist (spec ahead of code — the next iteration's gate)

The ai-jobs live run (2026-07-08) drove the r3 spec changes; the implementation
and this suite must catch up. Every item below is a REQUIRED test change; the
rule-coverage meta-test will force the fixture side automatically once the
rules land in the registry.

```text
T-r3-1  V-PATH-04 fixtures rewritten to the three clauses (docs/05): NEW pass
        fixtures — a commit APPENDING graph/commit JSONL during a lease passes;
        a docs ingest appending + creating docs/raw|text files passes; a
        `db rebuild` during a lease passes. Fail fixtures — JSONL prefix break;
        recorded bundle file modified; new file under graph/ or queue/.
        DELETE the committer-owned byte-identity tests (non-conformant).
T-r3-2  H10 moves from the lease-scan mapping to a verify-level test: append an
        unattributed graph record ⇒ verify exit 3 via V-COMMIT-04 replay.
T-r3-3  S2 updated per §8 (cache source DRES-only; REQUESTED pack composition;
        evidence-arrival staleness; cap = 3rd verdict + no-new-evidence +
        PR-initiated-only).
T-r3-4  S7 fixtures: every spine fact/mechanism node binds ≥2 EUs from ≥2
        documents (MSA-4/V-FRZ-02 r3); msa-check fixture updated; a 1-binding
        spine node now FAILS freeze (new refusal fixture).
T-r3-5  V-SWEEP-01: expand-beyond-layer-0 refused while a fact/mechanism seed
        claim lacks the sweep floor; passes after 2 angles recorded.
T-r3-6  V-TASK-04/05 unit tests: ingest ⇒ affected queued/blocked items stale;
        pack = REQUESTED ∪ top-12 MATCHED (a 25-EU project yields a ≤
        12+|REQUESTED| pack; requested EU with matcher score 0 still present).
T-r3-7  queue lifecycle: `validate result` from claimed performs complete
        implicitly (two events, one command); V-Q-01 table updated.
T-r3-8  failure observability: every validate_fail event carries per-rule
        detail naming a path/field (assert in the queue tests).
T-r3-9  `ui serve --auto-rebuild`: with the flag, a stale poll triggers rebuild
        (endpoint test); without it, the stale banner behavior is unchanged.
T-r3-10 worker templates: assert the shipped prompts/*.txt contain the r3
        SELF-CHECK / coverage / disconfirming-duty blocks (template drift test).
```

## 11. What Is Deliberately NOT Tested

```text
LLM judgment quality (whether a worker's scope_check was "right") — that is the
  human's spine review; the suite tests only that outputs obey contracts.
WebUI pixels — only the JSON endpoints are asserted.
Cross-platform behavior — v1 is POSIX-only by decree (docs/10 §2).
```

## 12. Search Program Worklist — S1 (Stage A, adopted 2026-07-08; docs/14)

S1 (Search Planning) is now binding (docs/00 adoption entry). Every item below is
a REQUIRED test change; once V-SP-* lands in the registry the rule-coverage
meta-test forces the fixture side automatically.

```text
T-S1-1  plan-compiler goldens: a fixed DocsRequest need + target scope compiles
        to a BYTE-EXACT search_plan.v1 under the determinism harness, incl. a CJK
        need (tokens() CJK-aware, docs/09 §0); the counter query is present in
        EVERY plan regardless of angle; facets/query templates exactly per docs/14.
T-S1-2  V-SP fixtures (one pass_ + one fail_ per rule): unaccounted qid (V-SP-01),
        skipped counter query (V-SP-02), docs_taken > urls_seen (V-SP-03),
        dishonest not_found with a productive entry (V-SP-04), plan ref that does
        not resolve / mismatches request (V-SP-05). docs_result.v2 round-trips
        (query_log replaces search_log); a v1 result still validates against v1.
T-S1-3  hostile: a worker that fabricates outcome counts (docs_taken > urls_seen)
        is rejected with V-SP-03 in failed_rules; `docs plan --request <DR>` emits
        the compiled plan and re-emits it byte-identically on a second call.
T-S1-back  the pre-S1 docs suite (V-DR, S2 docs loop, S3 cascade, ingest, cache)
        stays green: introducing docs_result.v2 + the plan compiler must not
        weaken or delete any existing docs assertion (evaluator diffs vs the gate
        tag). The DocsWorker dispatch path now attaches a compiled plan.
```

S3-lite (Source Registry, Stage A-lite; docs/16) — worklist:

```text
T-S3-1  ingest LEARNS: a Document ingested with a blocked query_log entry for its
        domain upserts a SourceProfile with blocked_direct=true and the workaround
        note; a second ingest appends a new profile version (latest-per-domain wins).
T-S3-2  tier mapping table golden (source_type → tier); a silent tier-lowering
        (new version lowers tier with no note) is rejected (V-SRC-03).
T-S3-4  provenance: every ingested doc carries provenance (retrieved_at,
        fetch_method ∈ enum, tier ∈ enum) [V-SRC-01]; a secondary_quote doc names
        quoted_via and the carrier exists, dangling quoted_via ⇒ V-SRC-02; the
        dispatch prompt's registry excerpt contains every T1 profile + every
        profile matching a plan-facet domain [V-SRC-05]. document.v2 round-trips;
        a v1 document still validates against v1.
T-S3-back  no regression (399 baseline + S1): document.v2 + registry learning must
        not weaken any existing ingest/V-DR/cascade assertion. V-SRC-04
        (triangulation) is Stage B — NOT built now; msa-check/freeze floors are
        unchanged from m5 until S4.
```

S2 (Search Orchestra, Stage A; docs/15, adopted 2026-07-08) — worklist:

```text
T-S2-1  merger goldens: crafted per-angle member results with (a) a duplicate
        content_hash across members, (b) a tracking-param URL variant that
        canonicalizes onto another member's page, (c) a duplicate EU (same doc,
        same normalized quote) collapse to the deterministic merged
        docs_result.v2 — byte-identical on re-merge of the same member set; every
        merged document/EU traces to a member (V-WAVE-02). canonical_url strips
        the frozen tracking list + default port + fragment, collapses duplicate
        slashes, strips one trailing slash.
T-S2-2  wave-verdict computation table: sufficient / followup / closed over the
        angle_covered combinations + primary_source_present + disconfirming +
        round; R_MAX=2 is never `followup` (no infinite loop); the follow-up
        round opens one member per no_attempt angle + one per expected_source
        (suggested_query → hint). CODE computes the verdict; the critic never does.
T-S2-3  hostile critic: a coverage_report smuggling documents/evidence_units is
        rejected with V-WAVE-03 (read-only); a closed-enum-incomplete form and
        >3 expected_sources also fire V-WAVE-03. Distinct member paths (V-WAVE-01),
        round cap + follow-up origin (V-WAVE-04), one DRES (V-WAVE-05) each have
        pass+fail assertions; a FakeCriticWorker joins tests/fakes/workers.py.
T-S2-4  `docs wave --fan` fans a DocsRequest into one member per angle (distinct
        outputs; the pre-existing single docs item is superseded); a wave that
        never covers an angle CLOSES at R_MAX recording the uncovered angle (no
        infinite loop) and ingests exactly ONE merged result (one DRES per wave);
        an all-covered wave is sufficient in round 1. `verify` exits 0 throughout.
T-S2-back  the 437-green pre-S2 suite stays green: a non-fan reactive request
        still runs as a single member unchanged; the S2 docs loop / cache / cap
        (test_s2_docs_loop) is untouched; the rule-coverage meta-test stays green
        (SCENARIO_COVERED or vrules per V-WAVE rule). Baseline in this worktree
        was S1-only (437), not the parent's assumed S1+S3-lite 457.
```
