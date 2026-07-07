# 01 Product Architecture Standard

PaperGraph is a coding-agent-native academic argument graph workflow engine. It turns a research topic and source materials into a verified, evidence-bound, freezeable argument structure.

It does not directly optimize for prose. It optimizes for the conditions under which prose becomes safe to write.

## Pipeline

```text
PaperSpec
  -> ProjectContract
  -> Multi-BFS Orchestration
  -> LogicNode / LogicEdge candidates
  -> ProofTask
  -> AgentTaskPacket
  -> ProofResult / EvidenceUnit
  -> Validator
  -> CommitDecision
  -> DocsRequest / BridgeProposal / Queue update
  -> Progressive Freeze
  -> Compiler Dry Run
  -> DraftMap
  -> Final Audit
```

## Module Boundaries

| Module | May Do | Must Not Do |
| --- | --- | --- |
| Phase 0 / PaperSpec | Define project type, scope, BFS plan, proof policy, docs policy | Generate final claims as proven |
| Logic | Propose one layer of candidate nodes/edges | Verify, cite, write prose, mutate frozen graph |
| Proof | Locally validate a node/edge/binding and suggest limited repairs | Write prose, change graph files, recursively expand bridges |
| Docs | Produce Document and EvidenceUnit records | Decide proof verdicts, create LogicNode, mutate graph |
| Validator | Enforce schema/path/invariant rules | Make research judgments beyond validation |
| Committer | Apply validated ProofResult to graph state | Call LLM, invent evidence, write prose |
| Freeze | Lock local/subtree/spine argument structures | Create new claims or evidence |
| Compiler | Check readiness and map frozen claims to draft sections | Add new logic, add citations, strengthen claims |
| Audit | Report binding/strength/scope issues | Rewrite manuscript |

## Paper Patterns

Supported first-version patterns:

```text
single_event_mechanism
parallel_case_bfs_then_merge
core_experiment_empirical
literature_debate_mapping
policy_design_memo
freeform_research_design
```

Pattern selection affects BFS topology, proof thresholds, docs policy, and compiler section plan. It must not bypass Proof or Commit.

## Multi-BFS Rule

PaperGraph is a spec-driven multi-BFS orchestration system, not one clever BFS loop.

Example:

```text
BFS-A-CASE and BFS-B-CASE may run in parallel.
BFS-MERGE waits for both case lanes to satisfy join conditions.
BFS-ALT handles alternative explanations.
BFS-DOCS handles evidence gaps triggered by Proof.
```

## Minimal Sufficient Argument

The system stops expansion only when the Minimal Sufficient Argument is complete:

```text
core question exists
core thesis exists
required case/mechanism nodes exist
required comparison/alignment nodes exist
required alternatives are handled or downgraded
core evidence bindings exist
compiler dry run reports no blocking gaps
```

Stop decisions must not use AI numeric scores.

## Lifecycle

Canonical node/edge lifecycle states:

```text
candidate
pending_proof
active
active_with_limits
reserve
parked_valid
future_research
background_only
needs_bridge
needs_docs
needs_split
needs_scope_narrowing
rejected_false
rejected_duplicate
out_of_scope
locally_frozen
subtree_frozen
spine_frozen
compiled
```

Canonical freeze states:

```text
not_frozen
local_frozen
subtree_frozen
spine_frozen
```

## First Implementation Scope

First implementation must prove this loop:

```text
A -> B
  -> ProofTask
  -> AgentTaskPacket
  -> local agent writes ProofResult(needs_bridge)
  -> Validator
  -> Committer
  -> bridge C/D candidate nodes enter queue
  -> CompilerDryRun reports gaps
  -> WebUI shows Logic Map + Queue Board
```

It must not implement unattended paper writing, hidden LLM proof calls, Neo4j, large GraphRAG indexing, or multi-agent debate.
