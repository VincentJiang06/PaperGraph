# Interface Spec Index

This directory contains implementation-facing interface contracts. It is separate from `docs/`, which describes product architecture and project-construction standards.

Use this split:

```text
docs/              why the system exists and how it should be organized
interface-specs/   exact contracts future implementation must expose
```

Canonical naming:

```text
Product name: PaperGraph
Python package: paperproof
CLI command: paperproof
Project root: data/projects/<project_id>/
```

## Interface Specs

Read in this order:

```text
interface-specs/01-state-storage-interface.md
interface-specs/02-graph-proof-docs-interface.md
interface-specs/03-agent-queue-interface.md
interface-specs/04-tooling-webui-cli-interface.md
interface-specs/05-handoff-package-interface.md
```

## Versioning

Every persisted payload must include:

```text
schema_version
project_id, unless the payload is repo-global
created_at, when the payload is an event/log record
```

Schema versions use:

```text
<object_name>.v1
```

Examples:

```text
logic_node.v1
proof_result.v1
work_item.v1
handoff_bundle.v1
```

## Contract Levels

```text
MUST: required for first implementation
SHOULD: recommended for first implementation
MAY: extension point
```

## Forbidden Interface Behavior

```text
No hidden LLM/API proof calls.
No agent worker direct graph mutation.
No numeric scoring fields for academic judgment.
No compiler-created claims or evidence.
No audit rewrite endpoint.
No non-rebuildable DB-only state.
```
