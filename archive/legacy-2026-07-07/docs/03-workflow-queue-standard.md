# 03 Workflow Queue Standard

This standard explains the workflow model. Exact queue payloads, statuses, and event schemas live in:

```text
interface-specs/03-agent-queue-interface.md
```

## Principle

PaperGraph is a parallel workflow with deterministic joins.

Workers may run concurrently, but shared state mutations must pass through gates:

```text
Validation Gate
Commit Gate
Freeze Gate
Compiler Gate
Audit Gate
```

## Multi-BFS Model

The system is not a single BFS loop. PaperSpec defines a BFS DAG:

```text
case lanes
comparison lanes
alternative-explanation lanes
docs/evidence lanes
compiler-gap repair lanes
```

Independent lanes may run in parallel. Merge lanes wait for dependency gates.

## Queue Model

Every unit of work should be observable as a queue item. The UI and CLI should never need to infer work only from scattered files.

Canonical queue families:

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

## Parallel Safety

Safe parallelism:

```text
many proof workers writing different outputs
many docs workers writing different outputs
many validators reading different outputs
multiple freeze workers only for different targets
```

Unsafe parallelism:

```text
multiple graph writers
workers editing graph directly
freeze racing with commit on the same target
compiler reading a half-mutated graph
```

## Join Rule

Join gates must read a snapshot and write a traceable event. If the snapshot is stale, the gate must refuse mutation and requeue work.
