# 00 Overview

PaperGraph is a research framework that runs **under Claude Code**. It replaces "write the paper linearly" with "build the argument as a graph, prove every edge, then compile prose once at the end."

## Core Thesis

Literary narration and linear text ordering are destructive to argument construction. So PaperGraph:

1. Represents the paper's ideas as a **Logic Graph** — claims are nodes, argumentative moves are directed edges.
2. Expands and verifies the graph layer by layer (BFS-style), producing a parallelizable **proof queue**.
3. Resolves each edge atomically with a **Proof Machine** — a bounded worker fills a fixed check form along an evaluation ladder ("in scope? evidence sufficient? inference holds?"); code computes the verdict from the form via a published decision table.
4. Caches every literature lookup in a **Docs Database** (memoized search) so evidence is reused, not re-searched, and citations cannot be hallucinated.
5. Produces **no prose until the final Compiler step**. Everything before that is structure, verdicts, and evidence bindings.

PaperGraph is not an autonomous paper-writing agent and not a RAG chatbot. It makes an argument verifiable, evidence-bound, and auditable **before** any prose exists.

## Component Map

```text
Topic Input file ──► Scoping ──► ProjectContract (fixed question, scope, outcome direction)
                                      │
                                      ▼
                              Logic Graph  (nodes / edges / layered BFS frontier)
                                      │  emits ProofTasks
                                      ▼
                              Proof Machine  (parallel bounded workers fill check forms;
                                              code computes verdicts by decision table)
                                      │  may request evidence
                                      ▼
                              Docs Database  (documents, EvidenceUnits, memoized search)
                                      │  validated results
                                      ▼
                              Committer  (the ONLY graph mutator)  ──► queue update, bridges
                                      │
                                      ▼
                              Freeze ──► Compiler (dry-run → draft map → prose) ──► Audit

WebUI monitor: read-only view over all of the above, at every stage.
```

## Runtime Model

- **Claude Code is the host.** The main session acts as Orchestrator; ProofWorkers and DocsWorkers are Claude subagents given bounded task files.
- **Files are the state.** All canonical state is JSON/JSONL under `data/projects/<project_id>/`. Agent chat text is never state; only validated output files are.
- **Deterministic code does the gates.** A small Python package `paperproof` provides schema validation, queue operations, commit/freeze/compile logic, and the WebUI server. Claude does judgment; code does bookkeeping.
- No API key is required for proof work: the system writes task files, Claude workers read them and write output files.

## Reading Order

```text
00-overview.md                 this file
01-topic-and-scoping.md        topic input, parsing rules, PaperSpec, ProjectContract
02-logic-graph.md              node/edge schemas, lifecycle, BFS expansion, spine, MSA
03-proof-machine.md            proof tasks, evaluation ladder, decision table, worker protocol
04-docs-database.md            documents, evidence, memoized search, matcher algorithm
05-workflow-and-queue.md       pipeline order, queue state machine, gates, parallelism
06-compiler-and-audit.md       freeze, dry run, section plan, draft map, prose, audit
07-runtime-and-tooling.md      storage layout, ids, snapshots, CLI, subagent wiring, WebUI
08-module-contracts.md         BINDING boundary contracts between all modules
09-verification.md             shared text algorithms, V-* rule registry, pipeline checks
10-v1-design.md                the concrete first version: scope, stack, CLI contracts,
                               worker prompts, build order, demo
11-test-suite.md               the executable test plan: fixtures, fakes, meta-tests,
                               milestone gates
12-webui-spec.md               the WebUI design: shell, tokens, views, components
```

Documents 01–07 describe modules; 08–12 bind them. On any boundary question (who writes what, what a gate accepts), `08-module-contracts.md` is authoritative. On any check, the rule IDs in `09-verification.md` are authoritative. On what v1 includes, `10-v1-design.md` is authoritative. On test structure, `11-test-suite.md` is authoritative. On WebUI design, `12-webui-spec.md` is authoritative (within the scope docs/10 §6 allows).

## Non-Negotiables

```text
1. JSON/JSONL files are canonical state; any DB or cache is derived and rebuildable.
2. Committer is the only module that mutates the Logic Graph.
3. Workers answer closed-enum check forms along the evaluation ladder; verdicts
   are computed by code from a published decision table. No numeric scores for
   academic judgment.
4. An edge with an inference gap gets at most 2 bridge-node proposals; workers
   never expand bridges recursively.
5. Docs produces evidence records only; it never sets proof verdicts or touches the graph.
6. No prose is generated before the Compiler stage; Compiler cannot create new claims or evidence.
7. Citations must resolve to a Document in the Docs Database. No invented citations.
8. Parallel workers must have disjoint output files; shared state changes go through gates.
```

## Naming

```text
Product name:      PaperGraph
Python package:    paperproof
CLI command:       paperproof
Source root:       src/paperproof/
Project data root: data/projects/<project_id>/
Example input:     examples/topic-input-p4.md
```

## Spec Revision r2 (2026-07-07)

This revision deepened every doc so a fresh implementation agent can execute without judgment calls. Normative changes an r1 reader must re-learn:

```text
Evaluation ladder + not_evaluated sentinel added to the check form (docs/03) —
  r1's form was unfillable for e.g. an out-of-scope fact node. Decision-table
  precedence changed: wellformed now outranks evidence; strength is uniformly
  "conditional iff assumptions non-empty" (nodes included).
Spine, MSA checklist items, lane completion (closing proposals), layer-0
  question/thesis seeding, and park/unpark are now mechanical (docs/02).
Lifecycle states change ONLY at commits; rejection cascades tombstone incident
  edges (state_reason=endpoint_rejected); queue gains a `cancelled` status.
CompileWorkers write agent_outputs/prose/ and `compiler ingest-prose` promotes
  to compiler/prose/ (r1 contradicted corollary C1). v1 Audit is fully
  mechanical; the semantic AuditWorker moved to v1.1.
CommitDecision, Tombstone, QueueEvent, verdict_record, DocsRequest-status
  schemas pinned (docs/08, 05, 03, 04); contract gains contract_version.
Matcher, request fingerprint cache, quote/paraphrase kinds, content_hash dedup
  pinned (docs/04). Shared text algorithms pinned (docs/09 §0).
CLI closed list extended: spec build --patch, graph park/unpark, queue
  expire/requeue; per-command contracts pinned (docs/10 §4).
docs/11-test-suite.md added: fixtures, FakeWorker API, 24 golden decision rows,
  hostile catalog, meta-tests, milestone gates.
```

## Spec Revision r2.1 (2026-07-07, correctness pass)

Two independent adversarial audits (an M0/M1 implementability walkthrough and a
step-by-step runtime simulation of S1/S2/S3/S7) were run against r2; every
confirmed finding was fixed. What an r2 reader must re-learn:

```text
Bridges are WIRED: the Committer creates bridge node X AND edge X→B (depends_on
  for definitions, supports otherwise), with lane/layer from the repaired
  edge's source; bridge rounds per edge capped at 2 (docs/08 B6).
MSA-9 added: the spine must contain ≥1 active fact/mechanism node — a cascade
  that hollows out the thesis's support now fails msa-check. Seed layers must
  connect seed chains to the thesis (demo adds EDGE-B-T).
Commit-gate currency is INPUT-SCOPED: proof commits check only target + 1-hop
  since the bundle snapshot (parallel proofs never invalidate each other);
  expansions check the whole graph; V-COMMIT-06 cancels in-flight items on
  tombstoned targets (docs/05, 08, 09).
V-PATH-04 is now the PREFIX rule: JSONL files must hash-match on their
  claim-time first-N bytes (append-only ⇒ concurrent engines can't trip it).
Caps dead-letter via a born-dead item: (created)→dead, op=dead_letter (docs
  cap and bridge cap). `queue fail` got legal edges; validated→stale/cancelled
  edges added; stale is proof-item-only.
Prose items: `compiler ingest-prose --work-item` = validate_pass + commit in
  one command. Docs items: request fields embedded in the prompt (no request
  file); `docs request` CLI added for Orchestrator-initiated requests;
  DRES- resolves via ingested_from stamps.
Edges: claim_version added (narrows work on edges); lane+layer inherited from
  the source node; id scheme carries -dep/-ref type markers; refutes edges may
  only target alternatives in v1 [V-EDGE-04].
Dry runs after a clean spine freeze report zero gaps BY CONSTRUCTION (docs/06
  reachability note) — the gap machinery is for unfreeze cycles and v1.1.
state_detail field added; stopword list frozen verbatim; CJK sentence
  splitting fixed; BFS-ALT's first layer is 1; spec build --patch shape pinned;
  milestone gates re-sequenced so no scenario needs later-milestone modules.
```
