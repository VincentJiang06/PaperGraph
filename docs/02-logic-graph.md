# 02 Logic Graph

The Logic Graph is where the paper's ideas live. Claims are nodes; argumentative moves are directed edges carrying a discrete strength class. The graph is expanded layer by layer (BFS-style) so proof work is naturally batched and parallelizable.

Design rule for all type systems in this doc: **one fact, one place**. A record's situation is fully described by `lifecycle_state` (+ reason) and, for proven records, `strength`. Nothing is encoded twice.

## LogicNode

```json
{
  "schema_version": "logic_node.v1",
  "node_id": "NODE-001",
  "project_id": "p4-ldi",
  "bfs_id": "BFS-MAIN",
  "layer": 1,
  "claim": "UK LDI strategies created margin-call liquidity pressure during rapid gilt yield movements.",
  "claim_version": 1,
  "node_type": "mechanism",
  "scope": {"period": "2022", "region": "UK"},
  "parents": [],
  "origin": {"kind": "seed", "source": "topic-input"},
  "lifecycle_state": "pending_proof",
  "state_reason": null,
  "state_detail": null,
  "strength": "unassessed",
  "language_limits": null,
  "assumptions": [],
  "evidence_bindings": [],
  "latest_proof_result_id": null,
  "frozen": false,
  "created_at": "2026-07-07T00:00:00Z"
}
```

Field semantics that are easy to get wrong:

```text
scope            object with optional keys period, region, actors, mechanisms —
                 same shape as the contract scope; compatibility rules docs/09 §0.
parents          node_ids this node was proposed under (BFS provenance, not edges).
origin.kind      seed | expansion | bridge   (source = topic-input, proposal id, or PR- id)
evidence_bindings  evidence_ids copied by the Committer from evidence_used when a
                 NODE_CHECK verdict computes to pass. This is THE binding the MSA
                 and Freeze check. Edges do not carry bindings — their evidence
                 lives in the verdict record (reachable via latest_proof_result_id).
latest_proof_result_id  PR- id of the newest verdict record for this node (set by
                 Committer on every proof commit).
state_reason     null unless lifecycle_state ∈ {needs_repair, rejected, parked};
                 always a bare enum token.
state_detail     object|null — structured companion to state_reason, e.g.
                 {"absorbed_into": "NODE-005"} on parked(absorbed) or
                 {"duplicate_of": "NODE-002"} on rejected(duplicate).
```

Edges carry `claim_version` too: a narrow repair on an edge replaces `edge_claim` and bumps it, exactly as node narrows do (docs/08 B6). For lane/layer gating (V-EXP-01, lane completion) an edge inherits **both the lane and the layer of its source node**; edges store neither field.

`node_type` — 6 values:

```text
question      the core research question
thesis        the intended answer
fact          an empirical claim; requires evidence
mechanism     a causal/functional claim; requires evidence
definition    a conceptual distinction
alternative   competing explanation to handle
```

(v2 reintroduces `comparison` together with merge lanes. "Limitations" are not nodes — they live in `language_limits` and `assumptions` on proven records.)

One node = one clear proposition. Prose paragraphs are never nodes. A `narrow` repair replaces `claim` text and bumps `claim_version`; the node is then re-proved from scratch.

**Updates are appends.** JSONL never rewrites: a state change appends a complete new record with the same `node_id` and the changed fields; "current state" is the last record per id. `created_at` on each appended version is the append time of THAT version (the record's birth time is the first version's `created_at`). This holds for every canonical JSONL file in the project.

## LogicEdge

```json
{
  "schema_version": "logic_edge.v1",
  "edge_id": "EDGE-001-002",
  "project_id": "p4-ldi",
  "source_node_id": "NODE-001",
  "target_node_id": "NODE-002",
  "edge_type": "supports",
  "edge_claim": "Margin-call pressure at LDI funds shows de-risking can convert solvency risk into liquidity risk.",
  "claim_version": 1,
  "lifecycle_state": "pending_proof",
  "state_reason": null,
  "state_detail": null,
  "strength": "unassessed",
  "language_limits": null,
  "assumptions": [],
  "frozen": false,
  "latest_proof_result_id": null,
  "created_at": "2026-07-07T00:00:00Z"
}
```

`edge_type` — 3 values, all pointing "argumentative flow" **into** the supported record:

```text
supports     source gives reason to believe target
refutes      source gives reason to reject target
depends_on   TARGET presupposes SOURCE (a definition node is the source;
             the claim that needs it is the target)
```

**v1 restriction [V-EDGE-04]: a `refutes` edge may only target an `alternative` node.** Otherwise an active refutes edge into a spine claim would be a live, unhandled objection that no MSA item catches. The idiomatic ways to kill an alternative remain contradicting evidence at its NODE_CHECK, or absorbing it via a narrow/language-limits on the spine claim; refutes edges document a refutation, they are never required. (v2 lifts this with real dialectic handling.)

(`elaborates` and `contrasts_with` are deferred to v2; in v1 a qualification is a `narrow` repair or a `depends_on` definition node, and comparison structure needs merge lanes anyway.)

## Lifecycle

One state machine for nodes and edges — 7 states:

```text
candidate      proposed, not yet queued
pending_proof  first-time proof work item open (queued, claimed, or blocked)
active         proven (strength says how strongly)
needs_repair   last verdict found a structural gap; state_reason = bridge | narrow
needs_docs     last verdict blocked on evidence
rejected       terminal; state_reason = contradicted | out_of_scope | duplicate
               | endpoint_rejected (edges tombstoned because an endpoint died)
parked         not needed for the minimal argument; state_reason = absorbed | not_needed
```

Freezing is **not** a lifecycle state — it is the boolean `frozen`, set only via Freeze (docs/06), meaningful only on `active` records, and blocking all further mutation.

**State semantics: "as of the last commit."** `lifecycle_state` changes only when the Committer writes — never when a queue item is claimed, unblocked, or rebuilt. Concretely: a record stays `needs_repair` or `needs_docs` while its repair/docs items run and while its re-proof item waits; the next proof commit moves it directly to `active` / `rejected` / `needs_*` again. There is no code path that flips `needs_repair → pending_proof` at "repair done" time, because unblocking is a queue-engine event, not a commit.

Transitions (all via Committer, from computed verdicts or administrative commits — docs/03, docs/08 B6):

```text
candidate ──enqueue (same commit that created it)──► pending_proof
pending_proof | needs_repair | needs_docs ──verdict──►
      active                (pass; strength = strong | conditional)
    | needs_repair          (repair items enqueued; reason = bridge | narrow)
    | needs_docs            (DocsRequests + docs items enqueued)
    | rejected              (tombstone appended)
active ──contract re-open (v1: manual) / unfreeze re-open──► pending_proof
active | candidate ──park (administrative commit)──► parked
parked ──unpark──► pending_proof (if ever proven) | candidate (if never proven)
node rejected ──cascade──► every non-rejected incident edge rejected
                           (state_reason=endpoint_rejected, tombstone, open items cancelled)
```

In v1 practice `candidate` rarely appears on disk: the expansion/bridge commit that creates a record also enqueues its check in the same CommitDecision, so the first stored state is `pending_proof`. `candidate` is stored only for alternatives deliberately created unqueued (not in v1) and for unparked never-proven records.

`rejected` is terminal; resurrecting an idea means a new candidate with a new id. History is never rewritten — every transition is a CommitDecision, and rejection appends a tombstone.

### Park / Unpark

Parking is an **administrative commit**, not a verdict: `paperproof graph park <id> --reason absorbed|not_needed [--into <record-id>]`.

```text
park requires:   record ∈ {active, candidate}, not frozen, reason given;
                 reason=absorbed additionally requires --into pointing at an
                 existing active record other than the target (that is the
                 mechanical check; whether it truly absorbs the alternative is
                 the Orchestrator/human judgment behind issuing the command) —
                 the Committer stores {"absorbed_into": <id>} in state_detail.
                 Parking clears strength to unassessed (V-GRAPH-03: strength
                 only on active records).
unpark:          paperproof graph unpark <id> — restores pending_proof (re-proof
                 enqueued) if the record was ever proven, else candidate.
Both append a CommitDecision (kind=park|unpark).
```

## Strength

Set only when a record becomes `active`; 3 values:

```text
unassessed   not yet proven (any non-active state)
strong       passes with no recorded assumptions
conditional  passes only with the recorded assumptions + language_limits
```

The rule is uniform for nodes and edges: **conditional iff `assumptions` is non-empty at pass** (docs/03 decision table row 8). There is no `weak` or `broken` strength — an unproven or refuted record is described by its lifecycle_state, not by a second field saying the same thing.

## BFS Expansion

Expansion proceeds in layers per BFS lane, following the `bfs_plan` DAG from the PaperSpec.

### Layer 0 (seeding)

The first proposal of `BFS-MAIN` is layer 0 and is special [V-EXP-06]:

```text
It must contain exactly one node_type=question node and exactly one
node_type=thesis node, plus one supports edge thesis→question ("the thesis,
if established, resolves the question"). It should also contain the seed
claims from the PaperSpec worth starting from. No other proposal, in any
lane, may contain question or thesis nodes.
```

### Layers 1..N

```text
1. Layer N nodes of the lane that are active form the frontier.
2. The Expander (an Orchestrator reasoning step) writes an ExpansionProposal file
   for one lane — one layer only, no deeper (schema and limits: docs/08 B3).
3. The proposal passes the Validator (V-EXP rules) and the Committer assigns real
   ids and appends the candidates — the Expander never writes graph files.
4. Every candidate enters the proof queue before it can support anything.
   NODE_CHECKs run first; an EDGE_CHECK is blocked until both endpoints are active
   (docs/03 ordering rule).
5. A lane whose depends_on lanes are not complete may not receive proposals [V-EXP-07].
```

### Lane completion

A lane is **complete** when a *closing proposal* — an ExpansionProposal with empty `nodes` and `edges` — has been committed for it AND no open work item targets a record of that lane. The closing proposal is the Expander's explicit "this lane needs no next layer"; committing it is recorded like any commit. Dependent lanes become proposable once all their `depends_on` lanes are complete.

Rules:

```text
The Expander proposes; it never sets verdicts, assigns ids, or mutates records.
Bridge nodes from needs_repair(bridge) are created AND wired by the Committer —
node X (lane/layer of the repaired edge's source node, parents=[target node],
origin.kind=bridge) plus edge X→target (depends_on for definitions, supports
otherwise) — they do not wait for the lane's expansion turn (docs/08 B6).
Expansion of a bridge node's own support happens through the normal next-layer
cycle — never recursively inside a proof task.
```

## The Spine

The spine is the mechanical object the MSA, Freeze, and Compiler all consume. Definition (computable, no judgment):

```text
Let Q be the unique question node, T the unique thesis node.
Let ACTIVE be the set of active records.

spine :=  {Q, T}
        ∪ {the supports edge T→Q}
        ∪ every node/edge from which T is reachable along ACTIVE
          supports/depends_on edges (i.e., the active ancestor closure of T,
          following edges source→target).
```

`refutes` edges never join the spine; rejected/parked records never join the spine. A record **touches** a record set C if it is in C, or is an edge with an endpoint in C, or is a node with a parent in C, or is an endpoint node of an edge in C (the symmetric clause matters for edge-only freeze closures). "Touches the spine" = touches C where C is the spine — this adjacency rule makes "no open work touching the spine" catch half-proved expansions growing into the argument.

## Stopping: Minimal Sufficient Argument

`paperproof graph msa-check` evaluates this checklist and prints per-item pass/fail (exit 0 iff all pass). Stop decisions are checklist-based — never an AI numeric score.

```text
MSA-1  exactly one question node and one thesis node exist; both active
MSA-2  the supports edge T→Q is active
MSA-3  every record in the spine is active (strength strong | conditional)
MSA-4  every fact/mechanism node in the spine has ≥1 evidence binding
MSA-5  every alternative node in the project is rejected, or parked with
       state_reason ∈ {absorbed, not_needed}
MSA-6  no work item with status ∉ {committed, cancelled} targets a record
       that touches the spine (dead letters included — they block)
MSA-7  every lane in bfs_plan is complete
MSA-8  the latest compiler dry run (if any) reports no blocking gaps —
       informational before first dry run, binding after
MSA-9  the spine contains at least one active fact or mechanism node — a
       thesis whose entire support was rejected leaves a vacuous spine
       {Q, T, T→Q}, and MSA-9 is what refuses to call that an argument
```

(The contract's `success_criteria` are deliberately NOT consumed by any MSA item or V-rule in v1 — they are the human's final-review checklist at `spec accept` and at draft review; v2 may compile them into MSA extensions.)
