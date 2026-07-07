# 01 State Storage Interface

This spec defines the project directory and persistence interface.

## Project Root

All project state lives under:

```text
data/projects/<project_id>/
```

The implementation MUST support this layout:

```text
specs/
  paper_spec.json
  project_contract.json
  agent_role_spec.json
  repo_convention.json

graph/
  logic_nodes.jsonl
  logic_edges.jsonl
  graph_state.json
  tombstones.jsonl

proof/
  tasks/
  context/
  proof_tasks.jsonl
  proof_results.jsonl

docs/
  documents.jsonl
  evidence_units.jsonl
  docs_requests.jsonl
  docspacks/
  raw/
  text/

agent_tasks/
  pending/
  running/
  done/
  failed/
  agent_task_packets.jsonl

agent_outputs/
  proof_results/
  docs_results/
  compiler_results/
  audit_results/

queue/
  work_items.jsonl
  leases.jsonl
  events.jsonl
  snapshots.jsonl
  dead_letters.jsonl

commit/
  commit_decisions.jsonl

freeze/
  frozen_items.jsonl
  msa_candidates.jsonl

compiler/
  compiler_dry_runs.jsonl
  draft_maps.jsonl

audit/
  audit_reports.jsonl

db/
  papergraph.duckdb
  index_manifest.json
```

## Canonical Files

Canonical state is JSON/JSONL. These files are authoritative:

```text
specs/*.json
graph/*.jsonl
proof/*.jsonl
docs/*.jsonl
agent_tasks/*.jsonl
agent_outputs/**
queue/*.jsonl
commit/*.jsonl
freeze/*.jsonl
compiler/*.jsonl
audit/*.jsonl
```

## Derived Files

Derived state MAY be deleted and rebuilt:

```text
db/papergraph.duckdb
db/index_manifest.json
graph layout cache
WebUI state cache
```

## JSONL Store Interface

The implementation MUST expose append/read operations equivalent to:

```text
append_jsonl(project_root, relative_path, payload) -> appended_record_ref
read_jsonl(project_root, relative_path) -> list[payload]
read_latest_by_id(project_root, relative_path, id_field) -> dict[id, payload]
```

Rules:

```text
append_jsonl creates parent directories if missing
append_jsonl validates project-relative paths
append_jsonl rejects upward traversal
append_jsonl writes one valid JSON object per line
read_latest_by_id resolves materialized latest state without deleting history
```

## Snapshot Interface

Join gates MUST create a snapshot record before mutating shared state:

```json
{
  "schema_version": "snapshot.v1",
  "snapshot_id": "GS-000001",
  "project_id": "demo",
  "created_at": "timestamp",
  "source_files": {
    "graph/logic_nodes.jsonl": {
      "sha256": "...",
      "rows": 42
    },
    "graph/logic_edges.jsonl": {
      "sha256": "...",
      "rows": 17
    }
  }
}
```

Committer and Freeze MUST reject stale snapshots when mutating shared state.

## DB Index Interface

The DB is a derived projection over JSONL. MVP MAY use DuckDB or SQLite.

Required DB tables:

```text
projects
logic_nodes_latest
logic_nodes_log
logic_edges_latest
logic_edges_log
proof_tasks
proof_results
agent_task_packets
docs_requests
evidence_units
work_items
leases
events
commit_decisions
freeze_items
compiler_runs
audit_reports
```

Every DB rebuild MUST write:

```json
{
  "schema_version": "db_index_manifest.v1",
  "project_id": "demo",
  "db_path": "db/papergraph.duckdb",
  "indexed_at": "timestamp",
  "source_files": {
    "graph/logic_nodes.jsonl": {
      "sha256": "...",
      "rows": 42
    }
  },
  "warnings": []
}
```

`paperproof db check <project_root>` MUST return `stale_index` when JSONL hashes differ from the manifest.
