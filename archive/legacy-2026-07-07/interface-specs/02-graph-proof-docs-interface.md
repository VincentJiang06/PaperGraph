# 02 Graph Proof Docs Interface

This spec defines the core research-state payloads. All models MUST reject unknown enum values and numeric scoring fields for academic judgment.

## LogicNode

MUST include:

```json
{
  "schema_version": "logic_node.v1",
  "node_id": "NODE-001",
  "project_id": "demo",
  "bfs_id": "BFS-A",
  "layer": 1,
  "claim": "Bounded claim text.",
  "node_type": "mechanism",
  "scope": {},
  "parents": [],
  "origin": {},
  "lifecycle_state": "candidate",
  "freeze_state": "not_frozen",
  "proof_state": {},
  "docs_bindings": [],
  "lineage_tags": []
}
```

Canonical `lifecycle_state`:

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

Canonical `freeze_state`:

```text
not_frozen
local_frozen
subtree_frozen
spine_frozen
```

## LogicEdge

MUST include:

```json
{
  "schema_version": "logic_edge.v1",
  "edge_id": "EDGE-A-B",
  "project_id": "demo",
  "source_node_id": "NODE-A",
  "target_node_id": "NODE-B",
  "edge_type": "supports",
  "edge_claim": "A supports B under a bounded scope.",
  "scope_transition": {},
  "required_assumptions": [],
  "origin": {},
  "lifecycle_state": "candidate",
  "freeze_state": "not_frozen",
  "proof_state": {}
}
```

## ProofTask

MUST include:

```json
{
  "schema_version": "proof_task.v1",
  "task_id": "PT-EDGE-A-B",
  "project_id": "demo",
  "bfs_id": "BFS-A",
  "layer": 1,
  "task_type": "EDGE_CHECK",
  "target": {
    "edge_id": "EDGE-A-B",
    "source_node_id": "NODE-A",
    "target_node_id": "NODE-B"
  },
  "context_pack_id": "CTX-EDGE-A-B",
  "docs_pack_id": "DOCSPACK-EDGE-A-B",
  "proof_policy": {
    "no_numeric_scores": true,
    "allow_partial_support": true,
    "allow_bridge_proposals": true,
    "max_bridge_nodes": 2,
    "do_not_write_paragraphs": true,
    "do_not_create_recursive_graph": true
  },
  "expected_output_schema": "proof_result.v1"
}
```

Allowed task types:

```text
NODE_CHECK
EDGE_CHECK
BINDING_CHECK
```

## EvidenceUnit

MUST include:

```json
{
  "schema_version": "evidence_unit.v1",
  "evidence_id": "EU-001",
  "project_id": "demo",
  "doc_id": "DOC-001",
  "source_type": "official_report",
  "citation": "Author, year, page or section",
  "summary": "What the source supports.",
  "support_direction": "supports",
  "can_cite_for": ["bounded claim text"],
  "cannot_cite_for": ["overbroad claim text"],
  "scope": {},
  "quote_or_paraphrase": null,
  "page_or_section": null,
  "lineage": {}
}
```

Docs outputs EvidenceUnit. Docs MUST NOT set Proof verdicts.

## ProofResult

MUST include:

```json
{
  "schema_version": "proof_result.v1",
  "proof_result_id": "PR-001",
  "task_id": "PT-EDGE-A-B",
  "project_id": "demo",
  "target_type": "edge",
  "target_id": "EDGE-A-B",
  "verdict": "needs_bridge",
  "support_level": "C",
  "scope_fit": "partial",
  "edge_sustainability": "not_directly_sustainable",
  "result_summary": "A alone does not sustain B.",
  "checks": {},
  "claim_status_update": {
    "recommended_status": "needs_bridge",
    "maximum_allowed_language": ["A may support a narrower claim."],
    "forbidden_language": ["A proves B."]
  },
  "bridge_proposals": [],
  "docs_requests": [],
  "commit_recommendation": {}
}
```

Allowed verdicts:

```text
supported
supported_with_limits
partially_supported
needs_bridge
needs_docs
needs_scope_narrowing
needs_split
contradicted
out_of_scope
duplicate_or_subsumed
```

Invariants:

```text
needs_bridge => 1-2 bridge_proposals
needs_docs => docs_requests is non-empty
target_type=edge => edge_sustainability is not not_applicable
target_type=binding => citation_alignment is set
non-rejected verdicts require maximum_allowed_language
non-rejected verdicts require forbidden_language
```

## CommitDecision

MUST include:

```json
{
  "schema_version": "commit_decision.v1",
  "commit_id": "COMMIT-001",
  "project_id": "demo",
  "based_on_proof_result": "PR-001",
  "input_snapshot_id": "GS-001",
  "actions": [],
  "new_queue_items": [],
  "new_docs_requests": []
}
```

Committer is the only module that may write graph mutations.

## FreezeItem

MUST include:

```json
{
  "schema_version": "freeze_item.v1",
  "freeze_id": "FREEZE-001",
  "project_id": "demo",
  "freeze_type": "local_freeze",
  "target_type": "node",
  "target_id": "NODE-001",
  "frozen_claim": "Bounded frozen claim.",
  "nodes": ["NODE-001"],
  "edges": [],
  "support_level": "B",
  "frozen_evidence_ids": ["EU-001"],
  "allowed_language": [],
  "forbidden_language": [],
  "remaining_limits": [],
  "allowed_section_roles": []
}
```

## CompilerDryRunReport

MUST include:

```json
{
  "schema_version": "compiler_dry_run.v1",
  "compiler_run_id": "CDR-001",
  "project_id": "demo",
  "input_graph_view": "frozen_graph",
  "input_snapshot_id": "GS-001",
  "writing_ready": false,
  "section_plan": [],
  "compiler_gaps": [],
  "reserve_activation_requests": [],
  "forbidden_actions": ["do_not_generate_new_logic"]
}
```

Compiler gaps may spawn queue items. Compiler MUST NOT create LogicNode or EvidenceUnit directly.
