# 05 Handoff Package Interface

This spec defines package-level handoff for model-to-model or worktree-to-worktree development.

## Handoff Bundle Layout

```text
handoff/<bundle_id>/
  manifest.json
  README_FOR_AGENT.md
  specs/
  queue/work_items.jsonl
  agent_tasks/pending/
  proof/tasks/
  proof/context/
  docs/docspacks/
  db/index_manifest.json
```

## Handoff Manifest

MUST include:

```json
{
  "schema_version": "handoff_bundle.v1",
  "bundle_id": "PKG-001",
  "project_id": "demo",
  "created_for": "claude-proof-batch",
  "allowed_task_ids": ["PT-0001", "PT-0002"],
  "allowed_write_paths": ["agent_outputs/proof_results/", "agent_notes/"],
  "forbidden_write_paths": ["graph/", "commit/", "freeze/", "compiler/", "src/"],
  "source_snapshot": {
    "logic_nodes_sha256": "...",
    "logic_edges_sha256": "...",
    "proof_tasks_sha256": "..."
  },
  "acceptance_commands": [
    "paperproof proof validate-result agent_outputs/proof_results/PT-0001.proof_result.json"
  ]
}
```

## Implementation Package Prompt

Every implementation package MUST be bounded:

```text
Package ID:
Objective:
Read first:
Allowed writes:
Forbidden writes:
Acceptance commands:
Stop rule:
Handoff notes:
```

Example:

```text
Package ID: QUEUE-001
Objective: Implement queue work item store, leases, and events for local JSONL state.
Read first:
- docs/00-standards-index.md
- interface-specs/03-agent-queue-interface.md
Allowed writes:
- src/paperproof/queue/
- tests/test_queue_contract.py
Forbidden writes:
- data/projects/*/graph/
- data/projects/*/commit/
- data/projects/*/freeze/
Acceptance:
- pytest tests/test_queue_contract.py
Stop rule:
- Do not implement DB indexer or WebUI in this package.
```

## Package Status

Each implementation package MUST append:

```text
handoff/package_status.jsonl
```

Payload:

```json
{
  "schema_version": "package_status.v1",
  "package_id": "QUEUE-001",
  "status": "ready_for_review",
  "owner": "codex-agent-queue",
  "changed_paths": [
    "src/paperproof/queue/",
    "tests/test_queue_contract.py"
  ],
  "acceptance_commands": [
    "pytest tests/test_queue_contract.py"
  ],
  "known_limits": [
    "Local file leases only; no distributed lock."
  ],
  "handoff_notes": "DB-001 should index queue/work_items.jsonl and queue/events.jsonl."
}
```

## Package IDs

Canonical implementation package IDs:

```text
SCHEMA-001
QUEUE-SPEC-LOCK
AGENT-PACKET-LOCK
QUEUE-001
DB-001
CLI-001
WEBUI-001
PROOF-001
DOCS-001
COMMIT-001
FREEZE-001
COMPILER-001
AUDIT-001
INTEGRATION-001
```

## Merge Order

```text
1. SCHEMA-001
2. QUEUE-SPEC-LOCK + AGENT-PACKET-LOCK
3. QUEUE-001
4. DB-001
5. CLI-001
6. PROOF-001 + DOCS-001
7. COMMIT-001
8. FREEZE-001
9. COMPILER-001
10. AUDIT-001
11. WEBUI-001
12. INTEGRATION-001
```
