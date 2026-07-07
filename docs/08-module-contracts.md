# 08 Module Contracts

This document is the binding contract layer between modules. Docs 01–07 describe each module from the inside; this doc pins down every **boundary**: who produces which artifact, who consumes it, under what pre/postconditions, and who is allowed to write what. When another doc and this doc disagree on a boundary question, this doc wins and the other doc must be fixed.

## 1. Artifact Ownership Table

Every canonical artifact has exactly one producer. Nobody else may create or mutate it.

| Artifact | File | Producer (only writer) | Consumers |
| --- | --- | --- | --- |
| Topic Input | `examples/*.md` (user path) | Human | Scoping |
| PaperSpec | `specs/paper_spec.json` | Scoping (`spec build`, code) | Expander, Compiler |
| ProjectContract | `specs/project_contract.json` (+ `specs/history/`) | Scoping + Human acceptance | Proof, Expander, Audit |
| LogicNode / LogicEdge | `graph/logic_nodes.jsonl`, `graph/logic_edges.jsonl` | **Committer only** | Expander, ProofTask builder, Freeze, Compiler, WebUI |
| Tombstone | `graph/tombstones.jsonl` | Committer | Audit, WebUI |
| GraphSnapshot | `graph/snapshots.jsonl` | Snapshot tool (code) | Committer, Freeze, Compiler |
| ExpansionProposal | `agent_outputs/expansions/*.json` | Expander step | Validator → Committer |
| ProofTask / ContextPack | `proof/tasks/*.json`, `proof/context/*.json` | ProofTask builder (code) | ProofWorker |
| DocsPack | `docs/docspacks/*.json` | DocsPack builder (code) | ProofWorker |
| ProofResult (check form) | `agent_outputs/proof_results/*.json` | ProofWorker | Validator → Committer |
| Verdict record | `proof/proof_results.jsonl` | Validator (computes verdict from form) | Committer, WebUI, trace |
| Document / EvidenceUnit | `docs/documents.jsonl`, `docs/evidence_units.jsonl` | Docs ingestor (code, from DocsWorker output) | DocsPack builder, Freeze, Compiler, Audit |
| DocsRequest | `docs/docs_requests.jsonl` | Committer or Orchestrator (create); docs engine (status updates) | DocsWorker |
| DocsResult | `agent_outputs/docs_results/*.json` | DocsWorker | Validator → Docs ingestor |
| WorkItem / QueueEvent | `queue/work_items.jsonl`, `queue/events.jsonl` | Queue engine (code) | Orchestrator, WebUI |
| CommitDecision | `commit/commit_decisions.jsonl` | Committer | Audit, WebUI |
| FreezeItem | `freeze/frozen_items.jsonl` | Freeze gate (code) | Compiler, Audit |
| CompilerDryRun | `compiler/dry_runs.jsonl` | Compiler dry-run (code) | Orchestrator, WebUI |
| DraftMap | `compiler/draft_maps.jsonl` | Compiler (code) | CompileWorker |
| ProseDraft (raw) | `agent_outputs/prose/*.md` | CompileWorker | `compiler ingest-prose` |
| ProseDraft (accepted) | `compiler/prose/*.md` | Compiler (`ingest-prose`, code) | Audit, Human |
| AuditReport | `audit/audit_reports.jsonl` | Audit (code; v1 fully mechanical) | Orchestrator, Human |
| DB index | `db/` | DB indexer (code) | WebUI, CLI queries |

Two hard corollaries:

```text
C1. Claude agents (Orchestrator included) never append to canonical JSONL directly.
    They call CLI commands; the code appends. The only Claude-written files are
    agent_outputs/** and agent_notes/**. (This is why CompileWorkers write
    agent_outputs/prose/ and ingest-prose copies into compiler/prose/.)
C2. "Validator → X" means the artifact is inert until validation passes. An
    unvalidated file in agent_outputs/ is not state; the ingestor/committer
    refuses files without a passing validation record.
```

## 2. Boundary Contracts

Each boundary below states: input, precondition, output, postcondition, and failure behavior. Validation rule IDs (`V-*`) are defined in `docs/09-verification.md`.

### B1: Human → Scoping (Topic Input)

```text
Input:         one Markdown topic file (format + parsing rules P1–P7 in docs/01)
Precondition:  all 9 required sections present, unique, non-empty  [V-SPEC-01]
Output:        specs/paper_spec.json + specs/project_contract.json
               (accepted_by_user=false, contract_version=1); derivation table docs/01
Postcondition: paper_type ∈ supported patterns; bfs_plan is a DAG  [V-SPEC-02..03]
On failure:    scoping reports missing/invalid sections; nothing is written.
```

### B2: Scoping → everything (ProjectContract acceptance)

```text
Input:         project_contract.json draft
Precondition:  human explicitly accepts (interactive step, `spec accept`)
Output:        contract with accepted_by_user=true, accepted_at set
Postcondition: contract is immutable; any edit = contract_version+1, old version
               archived to specs/history/, and every node/edge whose scope check
               depended on the old version goes back to pending_proof
               (re-opened by Committer as a batch commit; v1: manual re-open).
Blocking rule: NO graph expansion, proof task, or worker dispatch may run while
               the latest contract has accepted_by_user=false.  [V-GATE-01]
```

### B3: Expander → Commit gate (ExpansionProposal)

The Expander (an Orchestrator reasoning step) does **not** write graph files. It writes one ExpansionProposal file at `agent_outputs/expansions/<proposal_id>.json` (the proposal_id `EXP-<lane>-L<layer>` is a deterministic file-naming convention, not a code-assigned id; a validation retry overwrites the same file), which enters the same validate→commit path as ProofResults via `expand ingest`:

```json
{
  "schema_version": "expansion_proposal.v1",
  "proposal_id": "EXP-BFS-MAIN-L2",
  "project_id": "p4-ldi",
  "bfs_id": "BFS-MAIN",
  "layer": 2,
  "based_on_snapshot": "GS-000004",
  "nodes": [ { "claim": "...", "node_type": "mechanism", "scope": {}, "parents": ["NODE-001"] } ],
  "edges": [ { "source_ref": "NODE-001", "target_ref": "#0", "edge_type": "supports", "edge_claim": "..." } ]
}
```

`based_on_snapshot` is taken verbatim from `project status` (the one CLI payload that exposes the current GS- id).

```text
Precondition:  the lane's previous layer is fully committed (no open proof items
               in layer N of this lane)  [V-EXP-01]; snapshot current  [V-EXP-02];
               all depends_on lanes complete before a lane's FIRST proposal [V-EXP-07]
Postcondition: Committer assigns real node_ids/edge_ids, appends the records
               (first stored state pending_proof), enqueues NODE_CHECK/EDGE_CHECK
               work items (EDGE_CHECKs blocked_by their endpoint checks).
Limits:        ≤ 12 nodes per proposal; one layer only (= lane frontier + 1;
               first BFS-MAIN proposal is layer 0 and must contain exactly one
               question node, one thesis node, and the thesis→question supports
               edge [V-EXP-06]); edges may reference only existing node ids or
               nodes in this proposal ("#index")  [V-EXP-03..05]
Closing:       an empty proposal (nodes=[], edges=[]) declares the lane complete
               (docs/02); it is validated and committed like any other.
On failure:    proposal rejected with rule IDs; Expander may retry once with fixes.
```

### B4: ProofTask builder → ProofWorker (task bundle)

```text
Input:         one queued/stale proof work item
Output:        ProofTask + ContextPack + DocsPack (three files; docs/03, docs/04);
               rebuilds append a -rN revision, never overwrite (bundle immutability)
Postcondition: the bundle is self-contained — the worker needs no other file.
Staleness:     bundles embed based_on_snapshot; the COMMITTER marks unclaimed
               items stale when a commit mutates their target or a 1-hop
               neighbor (claim_digest drift alone does not stale a bundle);
               claim refuses stale items until rebuilt.  [V-TASK-01]
```

**1-hop neighborhood** (what `neighbor_nodes`/`neighbor_edges` must contain, [V-TASK-02]): for a NODE target — every non-rejected edge incident to it plus those edges' other endpoints; for an EDGE target — both endpoint nodes, every non-rejected edge incident to either endpoint, and those edges' other endpoints (this is how proven bridges become visible to an edge's re-proof).

ContextPack schema:

```json
{
  "schema_version": "context_pack.v1",
  "pack_id": "CTX-EDGE-001-002",
  "task_id": "PT-EDGE-001-002",
  "project_id": "p4-ldi",
  "based_on_snapshot": "GS-000004",
  "target": {},
  "neighbor_nodes": [],
  "neighbor_edges": [],
  "claim_digest": [ {"node_id": "NODE-001", "claim": "..."} ],
  "contract_scope": {},
  "forbidden_claims": [],
  "prior_results": []
}
```

`target` is the full latest node/edge record at the bundle snapshot, verbatim (the worker judges the claim text and reads nothing outside the bundle). `claim_digest` covers every non-rejected node in the project (duplicate detection needs global sight; v1 graphs are small). `prior_results` = verdict records for the same target (all revisions). DocsPack schema:

```json
{
  "schema_version": "docs_pack.v1",
  "pack_id": "DOCSPACK-EDGE-001-002",
  "task_id": "PT-EDGE-001-002",
  "project_id": "p4-ldi",
  "evidence_units": [],
  "documents_meta": []
}
```

An empty DocsPack is valid; it just means the worker cannot answer `evidence_check=sufficient` and will route to needs_docs on evidence-requiring targets.

### B5: ProofWorker → Validator (check form → computed verdict)

The heart of the system. The worker submits a **check form** (closed-enum answers along the evaluation ladder, `docs/03`); it never chooses a verdict. The Validator (a) checks form consistency (V-PR rules incl. ladder shape), then (b) **computes the verdict** by walking the decision table in `docs/03` (first match wins), and (c) appends the verdict record (`verdict_record.v1`, docs/03) — form + computed verdict + bundle paths — to `proof/proof_results.jsonl`, assigning the PR- id.

```text
Precondition:  worker held a valid lease on the work item.
Acceptance:    file at the declared output path, schema-valid, all V-PR-* pass,
               post-run path scan clean [V-PATH-04].
Postcondition: verdict record appended; work item -> validated; queued for commit.
               The decision table is total over ladder-valid forms: every valid
               form yields exactly one verdict.
On failure:    work item -> failed(validation), reasons recorded as rule IDs;
               retry ≤ 2 with the validation errors included in the retry prompt
               (same output path, overwritten); then dead-letter for human review.
Text rule:     worker chat/stdout is never parsed. File or nothing.
```

### B6: Verdict record → Committer (verdict→action map)

The Committer applies this table deterministically over the 4-verdict space. Same record + same snapshot ⇒ same actions.

| computed verdict | target lifecycle_state | strength | side effects |
| --- | --- | --- | --- |
| pass (strong) | active | strong | language_limits stored on target; NODE_CHECK: evidence_bindings set to the verdict's evidence_used (replaces prior); latest_proof_result_id updated (all rows) |
| pass (conditional) | active | conditional | as above + assumptions stored on target |
| needs_repair (bridge) | needs_repair (reason=bridge) | unassessed | bridge candidates created AND wired (see "Bridge wiring" below); re-proof item for the edge, blocked_by every bridge item |
| needs_repair (narrow) | needs_repair (reason=narrow) | unassessed | claim text replaced per proposal (`claim` on nodes, `edge_claim` on edges), claim_version+1; re-proof item enqueued (unblocked) |
| needs_docs | needs_docs | unassessed | DocsRequests appended (or cache-hit resolved, docs/04), docs_queue items enqueued; re-proof item blocked_by them; round-trip cap enforced (docs/04) |
| rejected (contradicted) | rejected (reason=contradicted) | unassessed | tombstone; CASCADE: every non-rejected incident edge → rejected(endpoint_rejected) + tombstone; its items in {queued, blocked, stale, failed} are cancelled now, and in-flight items (claimed/running/validating) finish their path and are cancelled at commit time by V-COMMIT-06 |
| rejected (out_of_scope) | rejected (reason=out_of_scope) | unassessed | tombstone with contract reference; same cascade |
| rejected (duplicate) | rejected (reason=duplicate) | unassessed | tombstone pointing at duplicate_of; same cascade |

```text
Precondition:  input snapshot current [V-COMMIT-01]; verdict record exists in
               proof/proof_results.jsonl [V-COMMIT-02]; target not frozen [V-COMMIT-03].
Postcondition: one CommitDecision listing every append performed; every new
               candidate has a proof work item; graph invariants hold (V-GRAPH-*);
               affected unclaimed bundles marked stale (B4).
Concurrency:   Committer is single-writer (commit/.lock); commits strictly serial.
On stale snapshot: refuse, requeue the commit item, rebuild dependent bundles.
```

**Bridge wiring.** A bridge proposal is a missing co-premise, and the Committer — never the worker — turns it into graph structure. For the repaired edge A→B and each proposed bridge X (1 or 2):

```text
append node X:  lane + layer = A's (the original edge's SOURCE node),
                parents = [B], origin = {kind: "bridge", source: <PR-id>},
                first stored state pending_proof
append edge X→B: edge_type = depends_on if X.node_type = definition,
                else supports; edge_claim = the deterministic synthesis
                "Bridge premise supporting the inference: <X.claim>" (satisfies
                V-EDGE-02 — it states X's role in the inference, not a
                restatement of either endpoint); first stored state pending_proof
enqueue NODE_CHECK(X); enqueue EDGE_CHECK(X→B) blocked_by NODE_CHECK(X)
re-proof item for A→B blocked_by ALL of the above (both bridges' node AND
                edge items)
```

This wiring is what makes the loop close mechanically: once X and X→B are active, X is a 1-hop neighbor of B — so the re-proof ContextPack contains it — and an active ancestor of the thesis through B — so it joins the spine (docs/02). Without the edge, a proven bridge would be invisible to both.

**Bridge-round cap:** like the docs cap (docs/04), bridge repairs per edge are capped at 2 rounds — a third `gap` verdict on the same edge appends no new bridges and the re-proof item is born dead ((created)→dead, op=dead_letter) for human review. This is the termination bound on the gap→bridge→re-proof cycle.

### B6b: Administrative commits

Everything below also goes through the Committer, with the same snapshot/lock discipline, `kind` recorded on the CommitDecision:

```text
expansion        apply a validated ExpansionProposal (B3)
park | unpark    docs/02 (park requires active|candidate, unfrozen; absorbed ⇒ --into)
freeze_batch     set frozen=true on a FreezeItem's targets (B8)
unfreeze_batch   set frozen=false + re-open proofs (B8)
contract_reopen  batch re-open after a contract version bump. v1 ships NO CLI
                 trigger for this (re-versioning automation is v1.1) — the kind
                 exists in the enum and is exercised via the committer API in
                 tests only, so schemas and goldens are v1.1-ready.
```

### CommitDecision and Tombstone (schemas)

```json
{
  "schema_version": "commit_decision.v1",
  "commit_id": "CD-000001",
  "project_id": "p4-ldi",
  "kind": "proof_verdict",
  "actor": "orchestrator",
  "input_ref": "PR-001",
  "based_on_snapshot": "GS-000004",
  "post_snapshot": "GS-000005",
  "actions": [
    {"action": "update_edge", "target_id": "EDGE-001-002", "detail": {"lifecycle_state": "needs_repair"}, "record": { "…": "the full logic_edge.v1 record as appended" }},
    {"action": "append_node", "target_id": "NODE-003", "detail": {"origin": "bridge"}, "record": { "…": "the full logic_node.v1 record as appended" }},
    {"action": "enqueue", "target_id": "WI-000007", "detail": {"queue": "proof_queue"}, "record": null}
  ],
  "created_at": "2026-07-07T00:00:00Z"
}
```

`kind` enum: `proof_verdict | expansion | park | unpark | freeze_batch | unfreeze_batch | contract_reopen`. `action` enum: `append_node | update_node | append_edge | update_edge | tombstone | enqueue | cancel_item | mark_stale | docs_request | set_frozen`. Each **graph-mutating** action (`append_node | update_node | append_edge | update_edge | tombstone | set_frozen`) carries `record` = the exact graph record it appended to `graph/*.jsonl`; non-graph actions set `record` to null. `detail` stays a human-readable summary. Replaying `actions` against the pre-snapshot must reproduce the post-snapshot exactly [V-COMMIT-04]: the replay reconstructs post-graph-state from **pre-state + the actions' `record` payloads only** (it never reads the appended lines), so a CommitDecision whose actions do not faithfully manifest the commit fails the check — the audit trail is genuinely replayable, not tautologically.

```json
{
  "schema_version": "tombstone.v1",
  "tombstone_id": "TS-001",
  "project_id": "p4-ldi",
  "target_type": "node",
  "target_id": "NODE-009",
  "reason": "out_of_scope",
  "duplicate_of": null,
  "commit_id": "CD-000014",
  "created_at": "2026-07-07T00:00:00Z"
}
```

`reason` enum: `contradicted | out_of_scope | duplicate | endpoint_rejected`.

### B7: Committer → Docs pipeline (DocsRequest) and back

```text
Committer appends DocsRequest(status=open) — unless the request-level cache
(fingerprint or matcher hit, docs/04) resolves it immediately as
fulfilled/"cache" — plus a docs_queue work item for real misses.
DocsWorker claims it, writes ONE DocsResult file:
```

```json
{
  "schema_version": "docs_result.v1",
  "request_id": "DR-001",
  "project_id": "p4-ldi",
  "documents": [ { "title": "…", "source_type": "official_report",
                   "origin": {"kind": "web", "url": "…"},
                   "text": "full extracted text inline for web sources",
                   "citation_key": "BoE2022FSR" } ],
  "evidence_units": [ { "doc_ref": 0, "location": "p.12", "kind": "quote",
                        "quote_or_paraphrase": "…", "summary": "…",
                        "support_direction": "supports",
                        "can_cite_for": ["…"], "cannot_cite_for": ["…"],
                        "scope": {} } ],
  "not_found": false,
  "search_log": ["queries actually run"]
}
```

```text
No id fields anywhere in a DocsResult (the ingestor assigns DOC-/EU-/DRES- ids).
Each evidence unit carries exactly one of doc_ref (index into this result's
documents) or doc_id (existing archived id) [V-DR-01].
Validator checks V-DR-*; Docs ingestor (code) archives raw/text files (writing
docs/raw + docs/text from inline text), dedups by content_hash, assigns ids,
appends documents + evidence_units, appends the DocsRequest status update
(fulfilled | not_found, fulfilled_by=DRES id), and unblocks the waiting
re-proof item.
not_found is a legitimate terminal state: the re-proof runs with the unchanged
DocsPack and the worker answers the form honestly (docs/04). Docs round-trips
per target are capped at 2, then dead letter for human review.
```

### B8: Graph → Freeze gate

```text
Input:         freeze command (target + level: local/subtree/spine)
Precondition:  V-FRZ-01 every record in the closure (defined per level, docs/06)
                        is active
               V-FRZ-02 every fact/mechanism node in the closure has ≥1 evidence binding
               V-FRZ-03 no work item with status ∉ {committed, cancelled} touches
                        the closure (adjacency rule docs/02; dead letters block)
               V-FRZ-04 spine_freeze: MSA checklist passes + `verify` exits 0
Postcondition: FreezeItem appended with the deduplicated, sorted union of
               language limits from the closure's records; frozen=true set on
               every target via a Committer batch commit (kind=freeze_batch) —
               Freeze itself never writes graph files.
Unfreeze:      human-only CLI action; appends FreezeItem(action=unfreeze,
               revokes=FRZ-id); Committer batch commit sets frozen=false and
               re-opens affected proofs.
```

### B9: Frozen graph → Compiler

```text
Dry run  — Input: snapshot with spine_freeze present. Output: CompilerDryRun with
           section_plan + gaps[] + writing_ready.
           Gap kinds + mechanical triggers: docs/06. Gap identity = (kind,
           target_id): each NEW gap spawns exactly one compile_queue item;
           re-runs deduplicate and auto-cancel items for resolved gaps [V-CDR-01];
           dry run creates no nodes/edges/evidence [V-CDR-02]; section plan
           covers every spine node exactly once [V-CDR-03].
DraftMap — only when writing_ready=true; fully derived (same inputs ⇒ identical
           bytes); schema + ordering rules docs/06.
```

### B10: DraftMap → CompileWorker → Audit

```text
CompileWorker input:  DraftMap only (plus the quoted EvidenceUnits it references).
CompileWorker output: agent_outputs/prose/<section_id>.md — one file per section,
                      annotation grammar per docs/06:
                      "...(claim: NODE-001)(cite: EU-001)".
Ingest:        compiler ingest-prose validates V-PROSE-01..04 and copies the
               accepted file to compiler/prose/<section_id>.md (producer: code).
Postcondition: prose contains no node_ids/evidence_ids absent from the DraftMap,
               no forbidden_language strings, full claim coverage. [V-PROSE-*]
Audit input:   compiler/prose/ + DraftMap + graph + evidence + contract.
Audit output:  AuditReport; v1 checks are fully mechanical (docs/06); findings
               are typed (binding|strength|scope|coverage) and each carries a
               location + target_id, so it can be routed as a compile_queue item
               mechanically.
```

## 3. Cross-Cutting Rules

### Single-writer summary

```text
graph/*            Committer (snapshots: snapshot tool invoked by Committer/init)
proof/*.jsonl      Validator;  proof/tasks|context     ProofTask builder
docs/*.jsonl       Docs ingestor / docs engine;  docs/raw docs/text  Docs ingestor
docs/docspacks/    DocsPack builder
queue/*            Queue engine
commit/*           Committer
freeze/*           Freeze gate
compiler/*         Compiler (incl. prose/ via ingest-prose)
audit/*            Audit
agent_outputs/**   the one worker whose task declares that exact path
agent_notes/**     any worker (scratch, never read as state)
specs/             Scoping (pre-acceptance only; history/ on version bump)
db/                DB indexer
```

### Snapshot discipline

Snapshots are cheap (hash + row count per graph file; mechanics docs/07) and the currency check is **input-scoped** (docs/05 §Commit Gate): proof-verdict commits require only the target + 1-hop neighborhood unchanged since the verdict's bundle snapshot (parallel proof commits never invalidate each other); expansion proposals require whole-graph currency [V-EXP-02]; administrative commits, Freeze, and Compiler read current state under the commit lock / from a fresh snapshot. This is the entire concurrency-control story of v1 — no locks beyond queue/commit locks and per-file append locks, no transactions.

### ID discipline

```text
Real ids are assigned only by code (Committer / ingestors / queue engine /
Validator), never by workers or the Expander. Worker-side references use local
refs ("#0", doc_ref) or existing ids taken verbatim from their input packs.
Formats + allocation: docs/07. This prevents id collisions between parallel
workers.
```

### Failure taxonomy

Every rejected artifact records machine-readable failure reasons:

```json
{ "failed_rules": ["V-PR-07"], "detail": {"V-PR-07": "inference_check=gap with 3 bridge repair_proposals (max 2)"} }
```

Retry policy is uniform: validation failure → ≤2 retries with errors in prompt → dead letter. Lease expiry → requeue with attempt+1 → after 3 attempts, dead letter. Dead letters surface in WebUI, block spine freeze if they touch the spine (V-FRZ-03), and re-enter only via human `queue requeue`.
