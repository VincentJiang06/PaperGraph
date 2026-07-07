# 04 Agent Handoff Standard

This standard explains how local agents participate. Exact task packet and handoff bundle fields live in:

```text
interface-specs/03-agent-queue-interface.md
interface-specs/05-handoff-package-interface.md
```

## Principle

PaperGraph should work with local coding agents by file handoff. Proof does not require a hidden API key path.

The system creates bounded task files. Agents read inputs, write outputs, and stop. Validators and committers decide whether outputs enter canonical state.

## Agent Roles

```text
ProofWorker: validates node/edge/binding
DocsWorker: extracts reusable EvidenceUnit candidates
AuditWorker: reports binding and scope issues
Codex Engineer: implements schemas, validators, storage, CLI, WebUI, DB
Human Supervisor: accepts research scope and major judgment calls
```

## Role Boundary

ProofWorker is not the author. It must not write essay prose, mutate graph files, invent citations, recursively expand bridge nodes, or use numeric scores.

DocsWorker is not the proof judge. It must not set proof verdicts.

Compiler is not a thinker. It maps frozen graph structures to draft plans and reports gaps.

Audit is not a rewriter. It reports violations.

## File-Based Acceptance

Agent chat text is not accepted system state. Only validated files are state.

An agent output is accepted only after:

```text
path safety passes
schema validation passes
domain invariants pass
ingestor appends the accepted object
the correct gate consumes it
```

## Parallel Agent Rule

Multiple agents can work in parallel when their output paths are disjoint and they do not write shared graph/commit/freeze/compiler state directly.
