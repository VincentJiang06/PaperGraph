# 05 Workflow and Queue

PaperGraph is a parallel workflow with deterministic gates. Workers run concurrently; every shared-state mutation passes through exactly one gate.

## Pipeline

```text
Topic Input
  -> Scoping (spec build + human accept)  specs/paper_spec.json, specs/project_contract.json
  -> LAYER-0 EXPANSION                     first BFS-MAIN proposal: question,
                                          thesis, thesis->question edge, seed
                                          fact/mechanism nodes (validated, committed)
  -> EVIDENCE SEEDING (the sweep, r3/v2.1) per fact/mechanism layer-0 node:
                                          docs request --target N ... --fan, then
                                          docs wave --request DR-x --fan
                                          (docs/04, docs/15) until V-SWEEP-01
  -> Expander writes deeper proposals      agent_outputs/expansions/*.json (validated, committed;
                                          first expansion BEYOND layer 0 gated by V-SWEEP-01)
  -> ProofTasks enqueued                  proof_queue
  -> ProofWorkers run in parallel         agent_outputs/proof_results/*.json (check forms)
  -> Validator                            form consistency + COMPUTES the verdict (docs/03)
  -> Committer                            graph mutation + CommitDecision + new queue items
  -> (loop: bridges/docs/next layer until MSA complete)
  -> Freeze                               lock spine structures
  -> Compiler dry run                     gap report; draft map when ready
  -> Compiler prose                       the ONLY prose-producing step
  -> Audit                                binding/scope/language check on the prose
```

**Order matters (v2.1, D4).** The sweep runs AFTER the layer-0 expansion, not
before it: sweep targets are layer-0 fact/mechanism *nodes* and
`docs request --target N` requires node N to exist. Only the first expansion
**beyond** layer 0 is gated on the sweep floor [V-SWEEP-01] — proofs never start
against an empty evidence base (the live run's root "too little evidence"
failure). (The pre-v2.1 "sweep before the expander" diagram was wrong.)

## Queues

All work is visible as WorkItems in `queue/work_items.jsonl`.

```text
proof_queue      NODE_CHECK / EDGE_CHECK tasks
docs_queue       open DocsRequests (incl. S2 wave members, target_type="request")
critic_queue     S2 CoverageCritic items (target_type="wave", docs/15) — one per
                 wave once its members are terminal; a bounded read-only worker
compile_queue    compiler gap-repair items and prose section tasks
commit_queue     a DERIVED VIEW, not stored items: work items in status
                 `validated`, FIFO by validation time, awaiting serial
                 `commit apply`. WorkItem.queue_name never equals commit_queue.
```

(Freeze and audit are deterministic gate runs invoked directly by the Orchestrator via CLI — they are events, not queued work, so they have no queues.)

WorkItem:

```json
{
  "schema_version": "work_item.v1",
  "work_item_id": "WI-000001",
  "project_id": "p4-ldi",
  "queue_name": "proof_queue",
  "status": "queued",
  "target_type": "edge",
  "target_id": "EDGE-001-002",
  "task_id": "PT-EDGE-001-002",
  "bundle": {
    "task_file": "proof/tasks/PT-EDGE-001-002.json",
    "context_pack": "proof/context/CTX-EDGE-001-002.json",
    "docs_pack": "docs/docspacks/DOCSPACK-EDGE-001-002.json"
  },
  "output_files": ["agent_outputs/proof_results/PT-EDGE-001-002.proof_result.json"],
  "blocked_by": [],
  "lease": {"claimed_by": null, "claimed_at": null, "expires_at": null, "manifest": null},
  "attempt": 1,
  "created_at": "2026-07-07T00:00:00Z",
  "updated_at": "2026-07-07T00:00:00Z"
}
```

`bundle` is null until `proof build-tasks` fills it. Per-queue item shapes: docs items carry `target_type="request"`, `target_id=DR-…`, `bundle=null` (the request's fields are embedded in the dispatch prompt — there is no per-request file); a **wave member** is a docs_queue item (`target_type="request"`) whose `task_id` is `SP-DR-x-<angle>[-rN-<origin-slug>]` — the angle plan id, from which the wave and angle resolve (docs/15, D2/D8); a **critic** item rides `critic_queue` with `target_type="wave"`, `target_id=WV-…`, `bundle=null` (its inputs — claim, plans, merged result, query_logs — are embedded by `docs render-prompt`); gap items carry `target_type="gap"`, `target_id="<kind>:<id>"`; prose items carry `target_type="section"`, `target_id=SEC-…`, `bundle={"draft_map": …}`. For MSA-6 / V-FRZ-03 "touching" purposes, a docs item counts as targeting its request's `target_id` record; a critic item does not touch the graph. `lease.manifest` is the claim-time canonical-directory hash map used by the post-run scan (V-PATH-04, §Parallelism). Status updates append a full new record per id, like every JSONL file.

## Status Machine

`status` enum (11 values):

```text
queued  claimed  running  validating  validated  committed
blocked  stale  failed  dead  cancelled
```

Complete transition table — these are the only legal edges [V-Q-01]. Every transition appends exactly one QueueEvent [V-Q-03].

| from → to | operation | actor / trigger |
| --- | --- | --- |
| (created) → queued | enqueue | Committer — or Compiler for gap/prose items — side effect (blocked_by empty) |
| (created) → blocked | enqueue | same actors (blocked_by non-empty) |
| (created) → dead | dead_letter | Committer: S4 SATURATION (docs/17, detail `{reason:"saturated", floor_met:…}`) or bridge-round cap reached — the re-proof item is born dead for human review. On a saturated+floor-MET conflict the same commit also records a `human_review` action (D1). The r3 docs round-trip cap is SUPERSEDED |
| blocked → queued | unblock | queue engine sweep: all blockers resolved |
| queued → claimed | claim | `queue claim --agent <name>` (writes lease) |
| claimed → running | heartbeat | first `queue heartbeat` (optional state; `complete` accepts claimed or running) |
| claimed \| running → queued | release | `queue release` (attempt unchanged) |
| claimed \| running → queued | expire | lease past expiry (attempt+1; >3 ⇒ dead) |
| claimed \| running → validating | complete | `queue complete` (output file exists) — OR performed implicitly by `validate result` (proof items), `docs ingest-result` / `docs wave-member` / `docs wave-resolve` (docs, wave-member, critic items), or `compiler ingest-prose` (prose items, v2.1 D14) (r3, below); `validate docs-result` stays a stateless V-PATH+V-DR dry check (no transition) |
| validating → validated | validate-pass | `validate result/proposal/docs-result`; for prose items, `compiler ingest-prose` runs V-PROSE as its validate-pass |
| validating → failed | validate-fail | same command; failed_rules recorded **with per-rule detail incl. the offending path** (r3 — the live run's bare rule ids made 5 identical failures undiagnosable from the event log) |
| claimed \| running \| validating → failed | fail | `queue fail` (manual: hung or hopeless worker); retry/dead per attempt as below |
| failed → queued | retry | automatic inside validate-fail when attempt < 3 (attempt+1) |
| failed → dead | dead-letter | automatic when attempt ≥ 3 (the docs/bridge caps use the born-dead edge above instead) |
| validated → committed | commit | proof items: `commit apply`; docs items: `docs ingest-result` (wave members: `docs wave-member`; critic items: `docs wave-resolve` — D2); prose items: `compiler ingest-prose` (the ingest commands thus emit validate_pass AND commit in one command). Only proof/graph commits produce a CommitDecision; ingest commits are recorded by their QueueEvent + the ingested records themselves |
| queued \| blocked → stale | invalidate | Committer: commit mutated target or 1-hop neighbor (proof items only) |
| validated → stale | invalidate | Committer refusal: target/1-hop mutated since the verdict's bundle snapshot (proof items only; rebuild + re-prove) |
| stale → queued \| blocked | rebuild | `proof build-tasks` (new bundle revision -rN) |
| queued \| blocked \| stale \| failed → cancelled | cancel | Committer: target tombstoned (e.g. endpoint_rejected cascade); Compiler dry-run: gap resolved; docs engine: `docs wave` supersedes a pending single docs item for the same DR — the wave owns the search (docs/15) |
| validated → cancelled | cancel | Committer: target tombstoned while the item was in flight (V-COMMIT-06) |
| dead → queued | requeue | `queue requeue` (human decision) |

Terminal states: `committed`, `cancelled`. `dead` is terminal-until-human. There are no other edges — in particular nothing ever moves backwards from `committed`, and no operation skips `validating`.

Blocked semantics:

```text
An EDGE_CHECK item is claimable only when both endpoint nodes are active at
sweep time; the engine maintains blocked_by as the currently-open work items
targeting the endpoints (re-pointing it when a re-proof item replaces a
committed one). A needs_docs re-proof item is blocked_by its docs items; a
bridge re-proof item is blocked_by the bridge NODE_CHECK items. The unblock
sweep runs at the start of every queue CLI command.
```

Lease parameters (v1 constants):

```text
lease duration 900s; heartbeat extends by another 900s from now; the expiry
sweep runs at the start of every queue CLI command (plus explicit `queue expire`).
Claim is atomic under the queue lock: an item never has two live leases [V-Q-02].
```

QueueEvent (`queue/events.jsonl`):

```json
{
  "schema_version": "queue_event.v1",
  "event_id": "QE-000001",
  "project_id": "p4-ldi",
  "work_item_id": "WI-000001",
  "op": "claim",
  "from_status": "queued",
  "to_status": "claimed",
  "actor": "proof-worker-1",
  "detail": {},
  "created_at": "2026-07-07T00:00:00Z"
}
```

`op` enum: `enqueue unblock claim heartbeat release expire complete fail validate_pass validate_fail retry dead_letter commit invalidate rebuild cancel requeue`. `detail` carries failed_rules, lease info, or cascade reasons. Edge cases pinned: `enqueue` events carry `from_status: null`; `release`/`expire` clear every lease field back to null; `heartbeat` is the one op that may leave status unchanged (running → running) and still emits an event.

## Parallelism Rules

Safe:

```text
many ProofWorkers, each with a distinct task_id and distinct output file
many DocsWorkers on distinct DocsRequests
validation of distinct output files
```

Unsafe (must never happen):

```text
any worker writing graph/, commit/, freeze/, compiler/, docs/*.jsonl, or queue/ files
two workers sharing an output file
freeze racing commit on the same target
compiler reading mid-commit graph state
```

Enforcement is mechanical, not honor-system — and it must not false-positive on the system's own parallelism. **r3 rewrite, grounded in the live run:** the r2 implementation added two checks beyond this spec — byte-identity on "committer-owned" JSONL (so every legitimate commit or docs ingest during any lease broke every in-flight validation: events QE-000048/51/64/101/104) and a new-file baseline over ALL canonical dirs (so engine-created bundle files, docs/raw|text archives, and `db rebuild` outputs tripped it too). Both are hereby ruled out; the scan is exactly this and nothing more:

```text
1. Workers get explicit allowed_write_paths (their declared output file plus
   agent_notes/**) in their prompt.
2. At claim time the queue engine records into lease.manifest: for every
   canonical JSONL file, (size, sha256); for every IMMUTABLE non-JSONL
   canonical file — specs/*.json, existing bundle files (proof/tasks|context,
   docs/docspacks), existing docs/plans/* SearchPlans and docs/merged/* merged
   results (S1/S2 immutable artifacts, docs/14/15), existing docs/raw +
   docs/text archives, compiler/prose/* — its sha256. db/** (incl. db/semantic/**)
   is NEVER in the manifest (derived, legitimately rewritten at any time).
3. `validate` checks [V-PATH-04], three clauses only:
   a. PREFIX: each recorded JSONL file's first `size` bytes still hash to the
      recorded sha256 — concurrent engines only append; a broken prefix means
      rewrite/truncation/history-editing. Appended lines are NOT inspected here
      (attribution is verify's job: V-COMMIT-04 replay + V-Q-03 make an
      unattributed append surface as corruption).
   b. IMMUTABLE: each recorded immutable non-JSONL file is byte-identical.
   c. STRICT-DIR NEW FILES: a file that did not exist at claim time appearing
      under specs/, graph/, queue/, commit/, freeze/, or audit/ fails — no
      engine ever creates new files there mid-lease. New files under
      proof/tasks|context, docs/docspacks|raw|text|plans|merged, compiler/,
      db/, agent_outputs/**, agent_notes/** are engine/worker-legitimate and
      pass (their integrity is enforced by verify's cross-reference sweep).
4. Every V-PATH-04 failure names the offending path in its detail.
```

## Gates

### Validation Gate

Deterministic code. Checks path safety, JSON schema, and domain invariants against the V-* rule registry (`docs/09-verification.md`). Invalid output → work item `failed` with the violated rule IDs **and per-rule detail (offending path / field)** recorded in the queue event and echoed into the retry prompt; the worker's text output is never consulted. Retry policy: ≤2 retries, then dead letter (`docs/08` §3).

**r3 ergonomic change (extended by v2.1):** the state-advancing validate paths
accept an item in `claimed` (or `running`) state and perform the `complete`
transition themselves (emitting both events) — the separate `queue complete` call
is optional. This is `validate result` for proof items; `docs ingest-result` for
single docs items (which thus emits complete + validate_pass + commit in one
call, docs/10 §4); `docs wave-member` / `docs wave-resolve` for wave-member and
critic items (D2); and `compiler ingest-prose` for prose items (D14). The
standalone `validate docs-result` is a stateless V-PATH+V-DR dry check and
performs no transition. The live run's claim→complete→validate ceremony left a
wide window in which concurrent engine activity aged the lease manifest;
collapsing it shrinks that window and removes the most common operator error.

### Commit Gate (Committer)

The only Logic Graph mutator. Single-writer: commits are applied serially under an exclusive lock on `commit/.lock`. The staleness precondition is **input-scoped** — this is what lets parallel proof work commit serially without invalidating itself:

```text
proof_verdict   precondition: no commit since the verdict's bundle snapshot has
                mutated the TARGET or its 1-hop neighborhood (whole-graph drift
                is fine). Violated → item validated → stale, bundle rebuilt,
                target re-proved. Target tombstoned meanwhile → item
                validated → cancelled (V-COMMIT-06). Target frozen → refuse
                (V-COMMIT-03).
expansion       precondition: the proposal's based_on_snapshot is current for
                the WHOLE graph [V-EXP-02] — expansion reasons about the global
                frontier. Violated → reject; Expander retries once.
administrative  no snapshot input; the Committer reads current state under the
                commit lock, so its view is current by construction.

Then: apply the action table deterministically (docs/08 B6 / B6b) → append one
CommitDecision recording input, actor, and every action → take the post-commit
snapshot → mark newly-affected unclaimed items stale / cancel items on
tombstoned targets.
```

Same input, same snapshot → same mutations, byte-identical CommitDecision under the determinism harness (docs/11 §3). No LLM inside the Committer.

### Freeze / Compiler / Audit Gates

See `06-compiler-and-audit.md`. Freeze locks structures; frozen items are immune to Logic mutation. Compiler and Audit read snapshots only.

## Layer Loop

The Orchestrator's steady-state loop, in actual commands (one iteration). After
the layer-0 expansion the sweep runs first (D4/D5): for each fact/mechanism
layer-0 node, `docs request --target N ... --fan` then `docs wave --request DR-x
--fan` (the wave sub-loop below), until V-SWEEP-01 clears the first expansion
beyond layer 0.

```text
paperproof queue expire                                  # crash recovery sweep
paperproof proof build-tasks --frontier                  # bundles for claimable + stale items
                                                         # (evidence-arrival staleness means
                                                         #  this also refreshes packs, docs/04)
for each claimable proof item (parallel, disjoint outputs):
    paperproof queue claim --queue proof_queue --agent <w>
    paperproof proof render-prompt --work-item <WI>      # fully-filled ProofWorker prompt (D11)
    <dispatch ProofWorker subagent>
    paperproof validate result <output> --work-item <WI> # completes + computes verdict
for each validated item (serial, FIFO):
    paperproof commit apply --result <verdict-record-ref>

# DOCS — a needs_docs re-proof opens a wave (or the sweep does). The S2 sub-loop:
paperproof docs wave --request DR-x [--fan]              # opens members (+ supersedes any single item)
for each wave member (docs_queue, parallel, disjoint outputs):
    paperproof queue claim --queue docs_queue --agent <w>
    paperproof docs render-prompt --work-item <WI>       # member prompt: angle plan + registry (D11)
    <dispatch DocsWorker subagent>
    paperproof docs wave-member <output> --work-item <WI># validate vs the angle plan + complete_member
# when EVERY member is terminal the engine AUTO-runs merge + opens the critic item (D2)
paperproof queue claim --queue critic_queue --agent <w>
paperproof docs render-prompt --work-item <WI>           # critic prompt: claim, plans, merged, query_logs
<dispatch CoverageCritic subagent>
paperproof docs wave-resolve <report> --work-item <WI>   # V-WAVE-03 + code computes the wave verdict
# followup verdict with a non-empty spec list opens round-2 members (loop); empty list closes now;
# sufficient/closed ⇒ merged result ingested (one DRES) + re-proof unblocked
# (a plain `docs ingest-result` REFUSES a wave-member item — it names `docs wave-member`)

when a lane's layer is fully committed:
    <Expander writes proposal>  → paperproof expand ingest <file>  (empty proposal closes the lane)
paperproof graph msa-check                               # loop exit test
```

A reactive `docs request` with no `--fan` still runs as a single DocsWorker
served by `docs ingest-result` (the pre-S2 path, unchanged); `docs ingest-result`
is only ever refused for a wave *member*.

After MSA: `freeze apply --level spine` → `compiler dry-run` → (gap repairs loop back into the queues) → `compiler draft-map` → CompileWorkers → `compiler ingest-prose` → `audit run`.
