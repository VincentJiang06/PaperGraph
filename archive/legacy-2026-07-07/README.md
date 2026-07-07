# PaperGraph Standards

PaperGraph is a coding-agent-native academic argument graph workflow engine.

It is not a normal RAG app and not an autonomous paper-writing agent. Its job is to make academic arguments verifiable, evidence-bound, queue-driven, freezeable, and auditable before prose is written.

## Repository State

This repository is now spec-only.

It intentionally contains:

```text
README.md
AGENTS.md
CLAUDE.md
CODEX.md
docs/
interface-specs/
```

It intentionally does not contain:

```text
implementation code
tests
virtual environment
demo runtime data
build metadata
CLI runtime
WebUI runtime
```

Future implementation agents must start from `docs/` for project-construction standards and `interface-specs/` for exact contracts. They must not assume any existing implementation exists.

## Canonical Naming

```text
Product name: PaperGraph
Python package: paperproof
CLI command: paperproof
Future source root: src/paperproof/
Project data root: data/projects/<project_id>/
```

## Standards

`docs/` describes principles, boundaries, and project construction:

1. [Standards Index](docs/00-standards-index.md)
2. [Product Architecture Standard](docs/01-product-architecture-standard.md)
3. [Data Contract Standard](docs/02-data-contract-standard.md)
4. [Workflow Queue Standard](docs/03-workflow-queue-standard.md)
5. [Agent Handoff Standard](docs/04-agent-handoff-standard.md)
6. [Tooling WebUI CLI DB Standard](docs/05-tooling-webui-cli-db-standard.md)
7. [Implementation Work Packages Standard](docs/06-implementation-work-packages-standard.md)
8. [Demo Acceptance Standard](docs/07-demo-acceptance-standard.md)

## Interface Specs

`interface-specs/` defines exact implementation-facing contracts:

1. [Interface Spec Index](interface-specs/00-interface-spec-index.md)
2. [State Storage Interface](interface-specs/01-state-storage-interface.md)
3. [Graph Proof Docs Interface](interface-specs/02-graph-proof-docs-interface.md)
4. [Agent Queue Interface](interface-specs/03-agent-queue-interface.md)
5. [Tooling WebUI CLI Interface](interface-specs/04-tooling-webui-cli-interface.md)
6. [Handoff Package Interface](interface-specs/05-handoff-package-interface.md)

## Core Pipeline

```text
PaperSpec
  -> ProjectContract
  -> Multi-BFS Orchestration
  -> LogicNode / LogicEdge candidates
  -> ProofTask
  -> AgentTaskPacket
  -> local agent output
  -> Validator
  -> CommitDecision
  -> Queue update
  -> Progressive Freeze
  -> Compiler Dry Run
  -> DraftMap
  -> Final Audit
```

## Non-Negotiables

```text
JSON / JSONL is canonical state.
SQLite / DuckDB is a derived index.
Proof runs through bounded local agent tasks, not hidden API calls.
Proof may propose at most two bridge nodes for a weak edge.
Docs produces EvidenceUnit and does not mutate the Logic Graph.
Committer is the only Logic Graph mutator.
Freeze is the only module allowed to lock argument structures.
Compiler cannot create new claims or evidence.
Audit reports issues and does not rewrite prose.
Multi-worker parallelism is a first-version requirement.
No AI numeric scoring for academic judgment.
```

## First Implementation Target

The first implementation should prove this loop:

```text
A -> B
  -> ProofTask
  -> AgentTaskPacket
  -> local Claude/Codex writes ProofResult(needs_bridge)
  -> Validator
  -> Committer
  -> bridge C/D candidate nodes enter queue
  -> CompilerDryRun reports gaps
  -> WebUI shows Logic Map + Queue Board
```

Implementation should be split by `docs/06-implementation-work-packages-standard.md` and must obey the contracts in `interface-specs/`.
