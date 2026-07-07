# 07 Runtime and Tooling

How the system actually runs under Claude Code, where state lives, and what the CLI/WebUI expose.

## Runtime Roles

```text
Orchestrator      the main Claude Code session. Runs scoping, expands layers,
                  dispatches workers, drives the loop. Uses CLI commands for all
                  state changes — never edits JSONL by hand.
ProofWorker       Claude subagent; one bounded proof task; writes one output file.
DocsWorker        Claude subagent; one DocsRequest; returns docs + evidence in one file.
CompileWorker     Claude subagent; prose for one section from a DraftMap.
paperproof (code) deterministic Python package: schemas, validator, queue, committer,
                  freeze, compiler dry-run, DB indexer, CLI, WebUI server.
Human             accepts the ProjectContract, resolves escalations/dead letters,
                  owns unfreeze and `queue requeue`.
```

Judgment (is this claim supported?) is Claude's; bookkeeping (is this file valid? what changes on commit?) is code's. Nothing requires an API key: workers are launched as Claude Code subagents reading/writing files.

## Storage Layout

All state under `data/projects/<project_id>/`:

```text
specs/
  paper_spec.json  project_contract.json
  history/                                  archived contract versions
graph/
  logic_nodes.jsonl  logic_edges.jsonl  tombstones.jsonl  snapshots.jsonl
proof/
  tasks/  context/  proof_results.jsonl
docs/
  raw/  text/  docspacks/
  documents.jsonl  evidence_units.jsonl  docs_requests.jsonl
agent_outputs/
  expansions/  proof_results/  docs_results/  prose/
agent_notes/                                 scratch space workers may write
queue/
  work_items.jsonl  events.jsonl  .lock
commit/
  commit_decisions.jsonl  .lock
freeze/
  frozen_items.jsonl
compiler/
  dry_runs.jsonl  draft_maps.jsonl  prose/
audit/
  audit_reports.jsonl
db/
  index.duckdb  index_manifest.json          (derived, rebuildable)
```

`paperproof project init <id>` creates exactly this tree (empty JSONL files included) plus nothing else.

Conventions:

```text
JSONL is append-only; "latest state" = last record per id; a state change appends
  a complete new record for that id; created_at on each appended version is the
  append time of that version. History is never rewritten.
Field conventions: every canonical JSONL record carries schema_version +
  project_id + created_at, with one exception — snapshot.v1 records omit
  project_id (implied by location). Bundle files (ProofTask, ContextPack,
  DocsPack) carry schema_version + project_id + their task correlation, but no
  created_at (they are derived, immutable artifacts). Where a shown schema and
  this convention disagree, this convention wins.
Timestamps are RFC 3339 UTC ("2026-07-07T09:00:00Z"). The clock is injectable:
  PAPERPROOF_NOW pins it for tests (docs/11 §3).
Canonical serialization: UTF-8, compact separators, no ASCII-escaping, schema
  field order, one record per line, trailing newline. Same data ⇒ same bytes.
Appends take an fcntl lock on the target file; the Committer and queue engine
  additionally hold commit/.lock / queue/.lock exclusively. v1 is POSIX-only.
Actor identity: --agent flag where present, else PAPERPROOF_ACTOR, else
  "orchestrator".
Derived db/ may be deleted anytime; `paperproof db check` reports stale_index
  on hash mismatch.
```

### ID formats

Ids are assigned only by code, by scanning the existing maximum per family (+1) — no counter files, deterministic under the test harness. Widths are fixed as shown; counters grow past the width naturally.

```text
NODE-001                    nodes
EDGE-001-002[-dep|-ref][-vN] edges: supports is bare; depends_on appends -dep,
                            refutes appends -ref (so all three types can
                            coexist between the same endpoints, V-EDGE-03);
                            -vN when the same (endpoints, type) recurs after
                            a rejection
EXP-<BFS>-L<layer>          expansion proposals — a FILE-NAMING convention
                            derived from lane+layer, not a code-assigned id
                            (the one exception to ID discipline; a validation
                            retry overwrites the same file)
PT-<target-id>[-rN]         proof tasks (-rN = any subsequent bundle for the
CTX-<target-id>[-rN]        same target: staleness rebuild OR re-proof)
DOCSPACK-<target-id>[-rN]   docs packs                  PR-001    verdict records
DOC-001  EU-001  DRES-001   docs objects                DR-001    docs requests
WI-000001  QE-000001        queue                       FRZ-001   freeze items
GS-000001  CD-000001        snapshots / commits         CDR-001   dry runs
TS-001                      tombstones                  DRAFTMAP-001  AUD-001
```

### Snapshots

`graph/snapshots.jsonl` records `{snapshot_id, files: {relpath: {sha256, rows}}, created_at}` over exactly `graph/logic_nodes.jsonl`, `graph/logic_edges.jsonl`, `graph/tombstones.jsonl`. A snapshot is **current** iff recomputing those three hashes matches. Snapshots are taken by the Committer after every commit (and by `project init` as GS-000001 over the empty files); every mutation gate refuses a non-current `based_on_snapshot`. Docs JSONL additions do not invalidate graph snapshots — bundle staleness is target-scoped instead (docs/05).

## CLI

Grammar: `paperproof <group> <command> [args]`. Global options: `--root <dir>` (default `./data`), `--project <id>` (or `PAPERPROOF_PROJECT`). Every command prints one JSON envelope (`{ok, command, data, errors, warnings}`) with the exit-code convention defined in `docs/10-v1-design.md` §4, which also holds the **authoritative, closed v1 command list with per-command contracts**. Overview of the surface:

```bash
paperproof project   init | status
paperproof spec      build [--patch] | accept | show
paperproof graph     list-nodes | list-edges | show | msa-check | park | unpark
paperproof expand    ingest <proposal-file>
paperproof proof     build-tasks --frontier | build-task <target-id>
paperproof docs      ingest | search | build-pack | request | ingest-result
paperproof queue     list | claim | heartbeat | release | complete | fail |
                     expire | requeue | events
paperproof validate  result | proposal | docs-result
paperproof commit    apply --result <ref>
paperproof freeze    apply | unfreeze
paperproof compiler  dry-run | draft-map | ingest-prose
paperproof audit     run --draft
paperproof db        rebuild | check
paperproof ui        serve --port 8420
paperproof verify    # whole-project invariant sweep (docs/09 §3)
paperproof trace     --node <id>   # sentence→evidence traceability chain
```

## Worker Dispatch

The Orchestrator dispatches a worker by:

```text
1. paperproof queue claim --queue <q> --agent <worker-name>
   → envelope.data carries the work item incl. bundle paths + output file.
2. Launch a Claude subagent from the fixed prompt template (docs/10 §5), filled
   with: the bundle file paths, allowed_write_paths, and the output file path.
3. Worker writes its output file and stops (its chat text is discarded).
4. paperproof queue complete <WI>; paperproof validate result <output> --work-item <WI>.
   On failure the item auto-retries (≤2 retries, violated V-* rules appended to
   the retry prompt via the retry suffix template) then dead-letters.
5. paperproof commit apply for validated results (serial).
```

Multiple workers run simultaneously whenever their task_ids and output files are disjoint. Heartbeats are optional for subagent workers (they normally finish inside one lease); long docs searches should heartbeat.

## WebUI

Read-only monitor over the whole system (plus queue claim/release buttons and db rebuild). Served by `paperproof ui serve`; reads the derived DuckDB with a stale-index banner (from `db check` at page load). Full design — shell, tokens, view layouts, components, test hooks — is `docs/12-webui-spec.md`; this section pins only the HTTP surface and the read model.

HTTP surface (FastAPI; all GET return JSON):

```text
GET  /api/overview     counts per queue+status, MSA checklist, contract status,
                       dead letters, stale_index flag
GET  /api/graph        nodes+edges (current state) for the Logic Map
GET  /api/record/{id}  the full latest canonical record behind any id
GET  /api/queue        work items with lease/attempt/blocked_by
GET  /api/events       queue events, newest first (paged ?after=QE-…)
GET  /api/evidence     documents joined with their EvidenceUnits
GET  /api/compiler     latest dry run + draft map + prose file list
GET  /api/trace/{node} the trace chain (same data as `paperproof trace`)
POST /api/queue/{id}/claim   body {agent}     (same semantics as CLI)
POST /api/queue/{id}/release
POST /api/db/rebuild
static /               one page: htmx/vanilla JS + vendored cytoscape.js
```

Views: Overview, Logic Map (color = lifecycle_state, border = frozen, edge style = strength; filters by lane/layer/state; click → detail drawer with raw JSON + proof history + trace), Queue Board, Evidence, Compiler, Events, Raw JSON drawer.

First-screen questions the Overview must answer:

```text
What is open? Who is working on what? What is blocked?
What can be committed? What is frozen? Is the index stale?
```

### Derived DB

`paperproof db rebuild` drops and recreates one DuckDB table per canonical JSONL file (`nodes, edges, tombstones, snapshots, verdict_records, documents, evidence_units, docs_requests, work_items, queue_events, commit_decisions, freeze_items, dry_runs, draft_maps, audit_reports`). Each table: `id`, `seq` (line number), `json` (full record), plus extracted hot columns (state/status/strength/queue_name/kind as applicable). Only the latest record per id appears in `*_current` views; full history stays in the base tables. `index_manifest.json` stores `{built_at, sources: {relpath: sha256}}`.
