# 05 Workflow and Queue

PaperGraph is a parallel workflow with deterministic gates. Workers run concurrently; every shared-state mutation passes through exactly one gate.

## Pipeline

```text
Topic Input
  -> Scoping (spec build + human accept)  specs/paper_spec.json, specs/project_contract.json
  -> Expander writes proposal             agent_outputs/expansions/*.json (validated, committed)
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

## Queues

All work is visible as WorkItems in `queue/work_items.jsonl`.

```text
proof_queue      NODE_CHECK / EDGE_CHECK tasks
docs_queue       open DocsRequests
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

`bundle` is null until `proof build-tasks` fills it. Per-queue item shapes: docs items carry `target_type="request"`, `target_id=DR-…`, `bundle=null` (the request's fields are embedded in the dispatch prompt — there is no per-request file); gap items carry `target_type="gap"`, `target_id="<kind>:<id>"`; prose items carry `target_type="section"`, `target_id=SEC-…`, `bundle={"draft_map": …}`. For MSA-6 / V-FRZ-03 "touching" purposes, a docs item counts as targeting its request's `target_id` record. `lease.manifest` is the claim-time canonical-directory hash map used by the post-run scan (V-PATH-04, §Parallelism). Status updates append a full new record per id, like every JSONL file.

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
| (created) → dead | dead_letter | Committer: docs round-trip cap or bridge-round cap reached — the re-proof item is born dead for human review |
| blocked → queued | unblock | queue engine sweep: all blockers resolved |
| queued → claimed | claim | `queue claim --agent <name>` (writes lease) |
| claimed → running | heartbeat | first `queue heartbeat` (optional state; `complete` accepts claimed or running) |
| claimed \| running → queued | release | `queue release` (attempt unchanged) |
| claimed \| running → queued | expire | lease past expiry (attempt+1; >3 ⇒ dead) |
| claimed \| running → validating | complete | `queue complete` (output file exists) |
| validating → validated | validate-pass | `validate result/proposal/docs-result`; for prose items, `compiler ingest-prose` runs V-PROSE as its validate-pass |
| validating → failed | validate-fail | same command; failed_rules recorded |
| claimed \| running \| validating → failed | fail | `queue fail` (manual: hung or hopeless worker); retry/dead per attempt as below |
| failed → queued | retry | automatic inside validate-fail when attempt < 3 (attempt+1) |
| failed → dead | dead-letter | automatic when attempt ≥ 3 (the docs/bridge caps use the born-dead edge above instead) |
| validated → committed | commit | proof items: `commit apply`; docs items: `docs ingest-result`; prose items: `compiler ingest-prose` (which thus emits validate_pass AND commit, two events in one command). Only proof/graph commits produce a CommitDecision; ingest commits are recorded by their QueueEvent + the ingested records themselves |
| queued \| blocked → stale | invalidate | Committer: commit mutated target or 1-hop neighbor (proof items only) |
| validated → stale | invalidate | Committer refusal: target/1-hop mutated since the verdict's bundle snapshot (proof items only; rebuild + re-prove) |
| stale → queued \| blocked | rebuild | `proof build-tasks` (new bundle revision -rN) |
| queued \| blocked \| stale \| failed → cancelled | cancel | Committer: target tombstoned (e.g. endpoint_rejected cascade); Compiler dry-run: gap resolved |
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

Enforcement is mechanical, not honor-system — and it must not false-positive on the system's own parallelism (queue events, serial commits, and other validations legitimately append to canonical files during a worker's lease). The mechanism is the **prefix rule**, which append-only storage makes possible:

```text
1. Workers get explicit allowed_write_paths (their declared output file plus
   agent_notes/**) in their prompt.
2. At claim time the queue engine records into lease.manifest: for every
   canonical JSONL file, (size, sha256); for every non-JSONL canonical file
   (specs/*.json, bundle files, compiler/prose/*), its sha256.
3. `validate` checks the prefix rule [V-PATH-04]: each recorded JSONL file's
   FIRST `size` bytes must still hash to the recorded sha256 — legitimate
   concurrent actors only append, so a broken prefix means someone rewrote,
   truncated, or edited history. Each recorded non-JSONL file must be
   byte-identical. New appended lines and new files are the engines' business
   and are audited by `paperproof verify`'s replay checks (V-Q-03,
   V-COMMIT-04), not by this scan.
```

## Gates

### Validation Gate

Deterministic code. Checks path safety, JSON schema, and domain invariants against the V-* rule registry (`docs/09-verification.md`). Invalid output → work item `failed` with the violated rule IDs recorded; the worker's text output is never consulted. Retry policy: ≤2 retries with the errors included in the retry prompt, then dead letter (`docs/08` §3).

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

The Orchestrator's steady-state loop, in actual commands (one iteration):

```text
paperproof queue expire                                  # crash recovery sweep
paperproof proof build-tasks --frontier                  # bundles for claimable + stale items
for each claimable proof item (parallel, disjoint outputs):
    paperproof queue claim --queue proof_queue --agent <w>
    <dispatch ProofWorker subagent with the prompt template (docs/10 §5)>
    paperproof queue complete <WI>
    paperproof validate result <output> --work-item <WI> # computes verdict or fails+retries
for each validated item (serial, FIFO):
    paperproof commit apply --result <verdict-record-ref>
for each open docs item (parallel):                      # same claim/complete/validate shape
    paperproof docs ingest-result <output>               # ingest + unblock re-proof
when a lane's layer is fully committed:
    <Expander writes proposal>  → paperproof expand ingest <file>  (empty proposal closes the lane)
paperproof graph msa-check                               # loop exit test
```

After MSA: `freeze apply --level spine` → `compiler dry-run` → (gap repairs loop back into the queues) → `compiler draft-map` → CompileWorkers → `compiler ingest-prose` → `audit run`.
