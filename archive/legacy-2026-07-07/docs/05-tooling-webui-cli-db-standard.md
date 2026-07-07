# 05 Tooling WebUI CLI DB Standard

This standard explains tooling goals. Exact CLI commands, Web API endpoints, and DB table names live in:

```text
interface-specs/04-tooling-webui-cli-interface.md
interface-specs/01-state-storage-interface.md
```

## Principle

Tooling exists to make the workflow observable, controllable, and handoff-safe. It is not the final reader-facing product UI.

## CLI Goal

The CLI should let agents and humans:

```text
create/verify a project
index/check derived DB state
list/claim/release/complete queue items
build and validate agent tasks
inspect graph/proof/docs state
run freeze/compiler/audit gates
create and verify handoff bundles
```

CLI output should be machine-readable by default.

## WebUI Goal

The WebUI must make parallel work visible:

```text
Logic Map
Queue Board
Parallel Lanes
Join Gates
Evidence Ledger
Compiler Gaps
Event Log
Raw JSON Drawer
```

The first screen should answer:

```text
What is open?
Who is working on what?
What is blocked?
What can be committed?
What is frozen?
What is stale?
```

## DB Goal

The DB is a local query index over JSONL. It supports filtering and UI performance. It is not canonical state.

Deleting the DB and rebuilding it from JSONL must be a normal operation.

## Safety

Tooling must not create hidden state. Any write operation must append canonical files or produce a rebuildable derived artifact.
