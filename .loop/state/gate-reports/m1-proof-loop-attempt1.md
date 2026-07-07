# Gate report — m1-proof-loop, attempt 1

## Generator result (Opus/high)
- `.venv/bin/python -m pytest -q`: **303 passed** (171 M0 + 132 M1); full gate exit 0 (orchestrator re-ran, confirmed). No M0 regression.
- M1 counts: decision_table 58 (incl. totality fuzz), v_pr 31, v_commit 14, v_exp 11, v_q 6, v_task 3, rule_coverage 4, integration 5.
- New src: committer/{decision_table,apply,replay}, queue/{engine,commands}, prooftask/builder, expander/ingest, graph/{model,commands}, verify.py, validate/proof.py + rules v_pr/v_exp/v_task/v_q/v_commit/v_node_edge.

## Generator OPEN DOC ISSUES → orchestrator disposition (post-evaluator)
1. V-PATH-04 vs concurrent commits (H10): committer graph appends byte-stable during a proof lease (no commit overlaps a proof [claim,validate] window). → evaluator judged.
2. V-PATH-04 stray-write scope: any agent_outputs/** allowed (V-PATH-01 pins the exact path separately). → evaluator judged.
3. Bridge edge_claim text: docs/08 B6 silent on the wired edge's edge_claim; Committer synthesizes deterministic "Bridge premise supporting the inference: <claim>". → **DOC-SYNC candidate** (pin it in docs/08 B6).
4. proof/.results.lock for PR-id alloc under parallel validators (S4): not in docs/07 layout. → **DOC-SYNC candidate** (add to docs/07 + note Validator holds it).

## Evaluator verdict — FAIL

Fresh adversarial review. Gate re-run clean (303 passed, exit 0; M0 subset 229 passed, no
regression). AST hollow-scan of all 12 M1 test files: no zero-assertion tests (the one
function with no bare `assert`, `test_v_q_02_second_claim_fails`, asserts via `pytest.raises`),
no `assert True`, no skip/xfail. The suite is overwhelmingly substantive — but one named
check in the correctness heart is hollow, and item 6 of my mandate asked me to verify exactly
this. That is the blocker.

### F1 (BLOCKING) — V-COMMIT-04 replay helper is tautological; it does NOT verify its stated property
`src/paperproof/committer/replay.py::replay_reproduces`. docs/09 V-COMMIT-04 and the module's
own docstring claim: "replaying actions against the pre-snapshot reproduces the post-snapshot."
The code does NOT do this. It slices the graph JSONL by the snapshot row-counts
(`lines[pre_n:post_n]`) and replays those *file lines* onto `latest_by_id(lines[:pre_n])`. That
is `latest_by_id(lines[:post_n])` by construction — i.e. `replayed == post_state` is an
algebraic identity that is ALWAYS true. `cd["actions"]` is never used to reconstruct any state;
it is consulted only for a final `len(graph_actions) == total_appended` COUNT check.
- Repro (verified): ran S1, took a proof_verdict commit (7 graph actions), appended a corrupted
  duplicate CommitDecision with every action `target_id="GARBAGE-999"` and `detail={"...":"BOGUS"}`
  (same count) → `replay_reproduces` still returns **True**. Dropping one graph action → False.
  So only the count discriminates; action *content* (target_id/detail) is never validated.
- Deeper: the CommitDecision `actions` carry only `{action, target_id, detail:{summary}}` (e.g.
  `{"action":"update_node","target_id":"NODE-001","detail":{"lifecycle_state":"active","strength":"strong"}}`),
  NOT the full appended record. So "replaying actions reproduces the post-snapshot" is not merely
  unimplemented — it is **unimplementable** from the current CommitDecision schema. Either the
  actions must carry enough to reconstruct records, or V-COMMIT-04's replay clause must be reworded
  (doc change per the "any deviation from docs/ updates the doc" rule).
- Severity note (fair): this is a verification-integrity defect, NOT a functional-behavior bug.
  The committer is deterministic and correct; the determinism property is independently and
  genuinely guarded by A14 (`test_determinism`, byte comparison across two roots — I reproduced
  it: 32 canonical files byte-identical) and `test_commit_decisions_byte_identical`. But
  V-COMMIT-04 is in the registry and rule-coverage (A15) reports it "covered" via these
  `replay.replay_reproduces` assertions in `test_v_commit.py` — a hollow check masquerading as
  coverage. In "the correctness heart of the system" a check that cannot fail must be fixed
  before the gate closes. Fix is well-scoped (thread `cd["actions"]`/enrich the action payload,
  or amend docs/09 V-COMMIT-04 + registry description).

### Independently verified sound (not "looks good" — reproduced)
- **Decision table (A8/A9), the top risk — SOUND.** All 24 golden fixtures (N01–N10, E01–E14)
  independently compute the exact docs/11 §6 verdict (24/24) and every one is ladder-valid
  (`ladder_check==[]`). Independent brute-force totality over the full enum product (node fact +
  definition, edge): 35 ladder-valid forms, 1085 ladder-invalid — every invalid one violates only
  a subset of {V-PR-05,14,15}; all 8 verdict classes reached across node+edge. The edge fuzz's
  `reached_verdicts == _VALID_VERDICTS` and `ladder_valid_count > 0` assertions genuinely kill
  both named failure modes (everything→ladder-invalid FAILS; everything→one-verdict FAILS).
  Precedence: row1 out_of_scope beats a form that also matches dup+contradicting+gap (first-match
  wins); wellformed(too_broad) outranks evidence(insufficient) → needs_repair(narrow); dup outranks
  wellformed; strength conditional iff assumptions.
- **Bridge wiring end-to-end (A11), second top risk — SOUND.** Ran S1 and inspected the graph
  JSONL: bridges NODE-005/006 (origin.kind=bridge, source node's bfs_id+layer, parents=[B]),
  edges C→B and D→B exist with edge_type=**depends_on** (definitions), both active; the EDGE-A-B
  re-proof item is blocked_by all FOUR bridge items (2 node + 2 edge checks); the re-proof
  `CTX-EDGE-003-004-r2.json` ContextPack neighbor_nodes = [002,003,004,**005,006**] — C,D present.
  I recomputed the spine per docs/02 (active ancestor closure of T along active supports/depends_on):
  both bridges land in the spine (C,D→B→T). No proven-but-unreachable bridge path found. Final
  EDGE-A-B active, conditional, scripted assumptions stored. V-PR-12 recompute over every verdict
  record: 0 mismatches.
- **Byte-determinism (A14) — SOUND.** Independently (not via the test) ran S1 twice into two temp
  roots under the same PAPERPROOF_NOW; all 32 files under graph/proof/queue/commit byte-identical
  (same file set, same SHA). No diff.
- **Hostile forms (A10) — SOUND + extended.** H04→V-PR-03, H05→V-PR-07, H06→V-PR-06, H08→V-PR-05,
  H11→V-PR-14, H12→V-PR-07, H13→V-PR-13, H14→V-PR-15, H15→V-PR-08, H17→V-PR-09, H18→V-PR-04, plus
  V-PATH H01/H02/H03/H10 — each caught by its NAMED rule (asserted). I added 6 NEW hostiles the
  catalog omits, all caught by the correct named rule: sufficient+empty evidence_used→V-PR-07;
  gap+0 bridges→V-PR-07; NODE assumptions+insufficient→V-PR-15; duplicate_of==target_id→V-PR-08;
  narrow→compound narrowed_claim→V-PR-11; deep-nested numeric→V-PR-03.
- **Committer determinism/replay (V-COMMIT-*) — mostly sound.** The 8 B6 verdict rows + B6b
  kinds + stale refusal (V-COMMIT-01) + frozen refusal (V-COMMIT-03) + no-op cancel (V-COMMIT-06)
  + rejection cascade are each asserted with real state checks. Byte-identical CommitDecisions
  across two runs confirmed. Only the V-COMMIT-04 replay clause is hollow (F1).
- **Queue 11-state machine (V-Q, A12/A13) — SOUND.** LEGAL table has no edges out of
  committed/cancelled and no (queued,commit); illegal transitions raise V-Q-01 (tested). Double
  claim of a claimed item raises (no two live leases). `file_lock` uses `fcntl.flock` on
  independent open file descriptions, so it genuinely serializes same-process threads → S4's
  parallel=4 over 8 items is a real concurrency test; ran it 5× with zero flakes, all 8 committed,
  each claimed exactly once in the event log. S5 expiry increments attempt and dead-letters at
  attempt>3 (appears in `queue list --status dead`); S6 rebuilds -r2 with the old -r1 bundle files
  still present and the verdict record citing -r2 paths.

### Judgment on the generator's 4 resolutions
1. **V-PATH-04 vs concurrent commits (H10)** — SOUND. Commits hold `commit/.lock` and the proof
   [claim,validate] window never overlaps a commit in the harness; the prefix-hash lease scan
   (V-PATH-04) correctly flags any append to a committer-owned file. Consistent with docs/05.
2. **V-PATH-04 stray-write scope (any agent_outputs/**)** — SOUND. V-PATH-01 separately pins the
   exact declared output path; allowing agent_outputs/** as the write sandbox is consistent with
   docs/05 and the lease manifest (`output_files + agent_notes/**`).
3. **Bridge edge_claim synthesis (DOC-SYNC)** — resolution is CORRECT BY CONSTRUCTION but exposes a
   latent gap. The synthesized `"Bridge premise supporting the inference: <claim>"` is provably
   distinct from both endpoints under casefold, so it satisfies V-EDGE-02 *in content*. HOWEVER
   V-EDGE-02 is **never actually enforced** on the wired edge: commit-time `_validate_post_graph`
   runs only `graph_record_checks`, which computes V-GRAPH-01..03 and never calls `edge02_ok`
   (`edge02_ok`/`edge01`-type helpers are effectively dead code in M1; V-EDGE/V-NODE are not in the
   registry). docs/09 lists V-EDGE "checked at commit time," but V-COMMIT-05 only names V-GRAPH-01..03
   and V-EXP-05 only re-checks nodes (V-NODE-02/03). Not a live bug (construction guarantees
   distinctness), but the doc should either (a) pin the synthesis formula in docs/08 B6 AND note
   V-EDGE-02 is only structurally guaranteed for bridges in M1, or (b) actually wire edge02_ok into
   the commit-time check. Flagging as a non-blocking latent gap.
4. **proof/.results.lock for PR-id allocation (DOC-SYNC)** — SOUND and necessary. Serializing
   read-then-append of the PR id under `.results.lock` correctly prevents duplicate PR ids when
   S4's validators run in parallel; without it the max+1 scan races. It does NOT mask a determinism
   bug: PR-id *assignment order* is nondeterministic under true parallel validation, but A14's
   byte-determinism contract is defined only over the serial harness (drain default parallel=1), and
   S4 deliberately asserts committed/no-double-lease/replayable — not byte-equality. Add it to
   docs/07 layout and note the Validator holds it, as the disposition says.

### Non-blocking observations
- V-EDGE-01..04 and V-NODE-01..03 are unenforced in the M1 pipeline (helpers exist but are not
  called at commit time; not in the registry). Acceptable for M1 scope per v_node_edge.py's header
  note, but docs/09's "checked at commit time" framing overstates M1 reality — reconcile in M2/M3.
- Determinism holds only on the serial path by design; if parallel validation is ever made
  canonical, PR-id order (and thus bytes) will diverge. Worth an explicit doc line.

Fix F1 (make V-COMMIT-04 replay reconstruct from actions, or reword the rule + enrich the action
payload) and re-run; everything else in M1 is genuinely sound and discriminating.

## Attempt 2 (fix) — orchestrator independent verification
- Full gate re-run: 312 passed, exit 0; full file-presence gate exit 0.
- Read the rewritten replay.py: reconstructs post from pre_state + action `record`
  payloads ONLY (records sourced from commit_decisions.jsonl, NOT the appended graph
  lines), compares to actual_post; null/missing record → False; count mismatch → False.
  Genuinely non-tautological (traced: id→GARBAGE-999 diverges reconstructed from actual).
- V-EDGE-02 now runs in graph_record_checks (commit + verify); fixtures added; rule_coverage green.
- proof/.results.lock → proof/.lock (docs/07). CommitDecision golden regenerated.
- Sending the same adversary back to confirm F1 closed + no regression.

## Evaluator verdict (attempt 2) — PASS

Same fresh adversary, re-verified independently with my own throwaway probes under /private/tmp
(did not trust the generator's tests). Full gate green: 312 passed, exit 0.

### F1 genuinely closed — the replay is no longer tautological (verified by construction + repro)
Read `committer/replay.py`: `by_file` is built ONLY from `cd["actions"][*]["record"]`; the appended
graph lines are read solely to compute `actual_post = latest_by_id(lines[:post_n])` and the pre-state
prefix — the changed portion is reconstructed from the CommitDecision's record payloads and compared
to the file-derived post. Two independent stores. My probe on a real S1 bridge commit (CD-000001,
7 graph actions, each action carries a full `record`):
- (e) honest commit → **True**
- (a) corrupt an action `record` id (→"ZZZ-999") → **False**
- (b) corrupt a record FIELD (flip `lifecycle_state`) → **False**
- (c) null a graph action's `record` → **False**
- (d) drop a graph action → **False**
- Independence (proves `actual_post` is file-derived, not self-compared): corrupt an appended graph
  line INSIDE the commit's `[pre_n, post_n)` window while leaving the CD record honest → **False**.
  (My first attempt at this returned True only because I had corrupted a later re-append of the same
  node OUTSIDE this commit's window; corrupting the in-window line — NODE-004 in `[0,4)` — correctly
  diverges.)
Cases (a)/(b) returning False also proves the reconstruction consumes the CD records, not the lines
(a line-based replay would have ignored the record corruption). No corruption slips through as True.
The CommitActionEntry `record` field is real and populated on every graph-mutating action.

### V-EDGE-02 is live at commit + verify (no longer dead code)
`graph_record_checks` now calls `edge02_ok` for every non-rejected edge. End-to-end via the actual
commit path: ingesting a layer-0 proposal whose `thesis→question` edge_claim verbatim-restates the
thesis claim is rejected — `expander.ingest` raises `V-COMMIT-05: post-commit graph invariants
violated` with **V-EDGE-02** in the rule list. The S1 bridge-synthesized edge_claim
("Bridge premise supporting the inference: …") passes it (full gate + S1 verify clean), so the
resolution-#3 latent gap from attempt 1 is now genuinely enforced, not just correct-by-construction.

### No regression on the attempt-1 sound parts
- Decision-table totality (slow fuzz) still green; the fuzz is untouched by the fix.
- Byte-determinism (A14) independently re-run across two temp roots: all 32 canonical files
  byte-identical (single SHA match). The aggregate hash differs from attempt 1 only because
  `commit_decisions.jsonl` now embeds the `record` payloads — expected; both runs are identical to
  each other, which is what A14 requires.
- S1 bridge wiring / spine, hostiles, queue: full suite 312 passed (was 303; +9 for the new replay
  and V-EDGE-02 coverage), no M0 regression.

Both findings from attempt 1 are genuinely fixed, docs updated to match (docs/08 §2b, `.results.lock`
→ `.lock` in docs/07). Everything I could break in the M1 proof loop now holds. M1 gate PASSES.
