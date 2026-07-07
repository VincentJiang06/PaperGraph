# Agent Protocol

All agents must treat `docs/` as the protocol source of truth.

Read first:

```text
docs/00-standards-index.md
docs/01-product-architecture-standard.md
docs/02-data-contract-standard.md
docs/03-workflow-queue-standard.md
docs/04-agent-handoff-standard.md
docs/05-tooling-webui-cli-db-standard.md
docs/06-implementation-work-packages-standard.md
docs/07-demo-acceptance-standard.md
interface-specs/00-interface-spec-index.md
```

Rules:

1. Read the assigned standard and task packet before acting.
2. Modify only allowed paths.
3. Produce required output files.
4. Run or document acceptance commands.
5. Never bypass validators.
6. Never edit frozen graph files.
7. Never invent citations.
8. Never use numeric scores for academic judgment.
9. Never let worker agents directly mutate the Logic Graph.
10. Preserve JSONL append-only semantics.

Parallel work is expected only when output paths are disjoint and shared state changes pass through the correct join gate.

When implementing, use `interface-specs/` for exact fields, CLI commands, queue events, API endpoints, and handoff bundle shapes.
