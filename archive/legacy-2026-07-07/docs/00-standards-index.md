# PaperGraph Standards Index

This repository is a spec-only handoff package. It contains no implementation, no tests, no virtual environment, and no demo runtime data.

The repository has two documentation layers:

```text
docs/              project-construction standards and design principles
interface-specs/   exact implementation-facing interfaces
```

Canonical naming:

```text
Product name: PaperGraph
Python package: paperproof
CLI command: paperproof
Future source root: src/paperproof/
Project data root: data/projects/<project_id>/
```

## Standards

Read these standards in order:

```text
docs/01-product-architecture-standard.md
docs/02-data-contract-standard.md
docs/03-workflow-queue-standard.md
docs/04-agent-handoff-standard.md
docs/05-tooling-webui-cli-db-standard.md
docs/06-implementation-work-packages-standard.md
docs/07-demo-acceptance-standard.md
```

Then read the exact interface specs:

```text
interface-specs/00-interface-spec-index.md
interface-specs/01-state-storage-interface.md
interface-specs/02-graph-proof-docs-interface.md
interface-specs/03-agent-queue-interface.md
interface-specs/04-tooling-webui-cli-interface.md
interface-specs/05-handoff-package-interface.md
```

## Non-Negotiables

```text
1. PaperGraph is not an autonomous paper-writing agent.
2. JSON / JSONL files are canonical state.
3. SQLite / DuckDB is a derived index only.
4. Proof is done by bounded local agent tasks, not hidden API calls.
5. Proof may propose bridge nodes but may not recursively expand subgraphs.
6. Docs produces EvidenceUnit; it does not mutate the Logic Graph.
7. Committer is the only Logic Graph mutator.
8. Freeze is the only module allowed to lock argument structures.
9. Compiler cannot create new claims or evidence.
10. Audit reports binding problems; it does not rewrite prose.
11. Multi-worker parallelism is a first-version requirement.
12. Commit and freeze joins must be deterministic.
13. No AI numeric scoring for academic judgment.
```

## Development Rule

Future implementation agents must not treat old experiments or generated outputs as source of truth. Standards in `docs/` define the design boundary; contracts in `interface-specs/` define exact implementation interfaces.
