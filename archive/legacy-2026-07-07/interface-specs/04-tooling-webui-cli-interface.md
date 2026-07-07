# 04 Tooling WebUI CLI Interface

This spec defines external tool interfaces.

## CLI Grammar

Canonical rule:

```text
paperproof <group> <command> <project_root> [options]
```

Project creation is the only exception.

## CLI Commands

### Project

```bash
paperproof project init <project_id> --root data/projects
paperproof project status <project_root>
paperproof project snapshot <project_root>
paperproof project verify <project_root>
```

### DB

```bash
paperproof db init <project_root>
paperproof db index <project_root>
paperproof db status <project_root>
paperproof db check <project_root>
paperproof db export <project_root> --out handoff/<bundle_id>
```

### Queue

```bash
paperproof queue list <project_root> --queue proof_queue --status queued
paperproof queue claim <project_root> --queue proof_queue --agent claude-proof-1 --limit 5
paperproof queue heartbeat <project_root> --work-item WI-000001
paperproof queue release <project_root> --work-item WI-000001 --reason blocked
paperproof queue complete <project_root> --work-item WI-000001 --output agent_outputs/...
paperproof queue events <project_root> --limit 50
```

### Agent

```bash
paperproof agent build-task <project_root> --proof-task PT-0001 --agent claude_code
paperproof agent validate-output <project_root> --task PT-0001
paperproof agent ingest-output <project_root> --task PT-0001
paperproof agent move <project_root> --task PT-0001 --to done
```

### Graph / Proof / Docs

```bash
paperproof graph list-nodes <project_root>
paperproof graph list-edges <project_root>
paperproof proof build-tasks <project_root> --layer 1
paperproof proof validate-task <path>
paperproof proof validate-result <path>
paperproof docs build-pack <project_root> --proof-task PT-0001
paperproof docs list-evidence <project_root>
```

### Freeze / Compiler / Audit

```bash
paperproof freeze local <project_root> --target NODE-001
paperproof compiler dry-run <project_root> --graph-view frozen_plus_reserve
paperproof compiler build-draft-map <project_root> --compiler-run CDR-001
paperproof audit final <project_root> --draft-map DRAFTMAP-001
```

### Handoff

```bash
paperproof handoff create <project_root> --include-db --out handoff/PKG-001
paperproof handoff verify handoff/PKG-001
paperproof handoff import handoff/PKG-001 --root data/projects
paperproof handoff summarize handoff/PKG-001
```

CLI output MUST be JSON by default.

## Web API

MVP endpoints:

```text
GET /api/state
GET /api/graph
GET /api/queues
GET /api/work-items/<id>
GET /api/agents
GET /api/evidence
GET /api/compiler-gaps
GET /api/events
POST /api/queue/claim
POST /api/queue/release
POST /api/db/reindex
```

`GET /api/state` MUST include:

```json
{
  "project_id": "demo",
  "project_root": "data/projects/demo",
  "status": "blocked_by_compiler_gaps",
  "stale_index": false,
  "counts": {},
  "open_work": {},
  "queue_items": [],
  "join_gates": {},
  "recent_events": []
}
```

## WebUI Required Views

```text
Overview
Logic Map
Queue Board
Parallel Lanes
Evidence Ledger
Compiler Gaps
Event Log
Raw JSON Drawer
```

## Logic Map Contract

Each node must expose:

```text
node_id
node_type
lifecycle_state
freeze_state
bfs_id
layer
claim
```

Each edge must expose:

```text
edge_id
source_node_id
target_node_id
edge_type
lifecycle_state
latest_proof_verdict
edge_claim
```

Filters:

```text
bfs_id
layer
lifecycle_state
freeze_state
node_type
proof verdict
```

## Queue Board Contract

Each queue card must show:

```text
work_item_id
queue_name
target_id
task_id
status
claimed_by
attempt
blocked_by
next_action
created_at
updated_at
```

Status colors follow `interface-specs/03-agent-queue-interface.md`.
