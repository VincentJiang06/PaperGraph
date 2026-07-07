# 03 Agent Queue Interface

This spec defines task packets, work items, leases, and events.

## AgentTaskPacket

MUST include:

```json
{
  "schema_version": "agent_task_packet.v1",
  "task_id": "PT-EDGE-A-B",
  "project_id": "demo",
  "agent_target": "claude_code",
  "fallback_agent": "codex",
  "task_kind": "proof_edge_check",
  "input_files": [
    "proof/tasks/PT-EDGE-A-B.json",
    "proof/context/CTX-EDGE-A-B.json",
    "docs/docspacks/DOCSPACK-EDGE-A-B.json"
  ],
  "output_files": [
    "agent_outputs/proof_results/PT-EDGE-A-B.proof_result.json"
  ],
  "allowed_write_paths": [
    "agent_outputs/proof_results/",
    "agent_notes/"
  ],
  "forbidden_write_paths": [
    "graph/",
    "commit/",
    "freeze/",
    "compiler/",
    "src/"
  ],
  "success_commands": [
    "paperproof proof validate-result agent_outputs/proof_results/PT-EDGE-A-B.proof_result.json"
  ],
  "prompt_file": "agent_tasks/pending/PT-EDGE-A-B.md",
  "status": "pending"
}
```

Allowed `agent_target`:

```text
claude_code
codex
manual
```

Allowed Proof task kinds:

```text
proof_node_check
proof_edge_check
proof_binding_check
```

## WorkItem

MUST include:

```json
{
  "schema_version": "work_item.v1",
  "work_item_id": "WI-000001",
  "project_id": "demo",
  "queue_name": "proof_queue",
  "priority": "normal",
  "status": "queued",
  "bfs_id": "BFS-A",
  "layer": 1,
  "target_type": "edge",
  "target_id": "EDGE-A-B",
  "task_id": "PT-EDGE-A-B",
  "input_paths": ["proof/tasks/PT-EDGE-A-B.json"],
  "output_paths": ["agent_outputs/proof_results/PT-EDGE-A-B.proof_result.json"],
  "blocked_by": [],
  "unblocks": ["WI-COMMIT-EDGE-A-B"],
  "lease": {
    "claimed_by": null,
    "claimed_at": null,
    "expires_at": null
  },
  "attempt": 1,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

Allowed `queue_name`:

```text
logic_frontier
proof_queue
agent_task_queue
docs_queue
validation_queue
commit_queue
freeze_queue
compiler_gap_queue
audit_queue
```

Allowed `status`:

```text
queued
claimed
running
waiting_agent
waiting_docs
validating
needs_bridge
needs_docs
blocked
failed
validated
committed
frozen
done
stale
```

## QueueEvent

MUST include:

```json
{
  "schema_version": "queue_event.v1",
  "event_id": "QE-000001",
  "project_id": "demo",
  "work_item_id": "WI-000001",
  "event_type": "status_changed",
  "from_status": "queued",
  "to_status": "claimed",
  "actor": "claude-proof-1",
  "created_at": "timestamp",
  "metadata": {}
}
```

Allowed event types:

```text
created
claimed
heartbeat
released
expired
status_changed
completed
failed
dead_lettered
```

## LeaseEvent

MUST include:

```json
{
  "schema_version": "lease_event.v1",
  "lease_event_id": "LE-000001",
  "project_id": "demo",
  "work_item_id": "WI-000001",
  "event_type": "claimed",
  "claimed_by": "claude-proof-1",
  "claimed_at": "timestamp",
  "expires_at": "timestamp",
  "reason": null
}
```

## Queue Operation Semantics

```text
claim: queued -> claimed
heartbeat: extends lease if claimed_by matches
release: claimed/running -> queued or blocked
complete: running/validating -> validated/done
fail: any active state -> failed
expire: claimed/running with expired lease -> queued or stale
```

Agents MUST write only their output files. They MUST NOT append queue events directly unless the task explicitly grants queue tool permissions.
