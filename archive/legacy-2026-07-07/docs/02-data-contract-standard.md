# 02 Data Contract Standard

This standard explains how PaperGraph thinks about data. Exact fields and payload shapes live in:

```text
interface-specs/01-state-storage-interface.md
interface-specs/02-graph-proof-docs-interface.md
```

## Principle

PaperGraph must be inspectable and recoverable from local files. No critical project state may live only in memory, a UI cache, or a database index.

## Canonical State

Canonical state is:

```text
JSON
JSONL
Markdown task prompts
raw/text source files
agent output files
```

Append-only logs are preferred for anything that records judgment, mutation, or historical workflow:

```text
ProofResult
CommitDecision
EvidenceUnit
AgentTaskPacket
WorkItem
QueueEvent
FreezeItem
AuditReport
```

## Derived State

SQLite / DuckDB is allowed only as a derived projection for query speed, WebUI filtering, and handoff summaries. It must be rebuildable from JSONL.

If canonical JSONL and DB disagree, JSONL wins and the DB is stale.

## Contract Boundary

The data layer must separate:

```text
claims
edges
proof judgments
evidence records
queue state
committed mutations
frozen structures
compiler readiness
audit findings
```

No module should smuggle one category into another. For example, EvidenceUnit does not contain a proof verdict, and CompilerDryRun does not create LogicNode.

## Schema Rule

All persisted objects must have controlled schemas. Enum values are preferable to arbitrary strings where they affect workflow state.

For implementation-facing schema details, use the interface specs rather than duplicating fields here.
