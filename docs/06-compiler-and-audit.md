# 06 Freeze, Compiler, and Audit

The endgame: lock the argument, check readiness, produce prose exactly once, audit it.

## Freeze

Freeze locks argument structures so the Compiler works on stable input. Freeze never creates claims or evidence.

Freeze levels and their **closures** (the record set actually locked):

```text
local_freeze     closure = the one target node/edge
subtree_freeze   closure = the target node + its active ancestor closure
                 (every node/edge from which the target is reachable along
                  active supports/depends_on edges — same walk as the spine
                  definition in docs/02, rooted at the target)
spine_freeze     closure = the spine (docs/02) — precondition for compiling
```

Freeze preconditions (checked deterministically; rules V-FRZ-01..04 in docs/09):

```text
every record in the closure is active (strength strong or conditional)
every fact/mechanism node in the closure has ≥2 evidence bindings from ≥2
  distinct documents (r3; matches MSA-4 / V-FRZ-02)
no work item with status ∉ {committed, cancelled} touches the closure
  (touching: the adjacency rule in docs/02 — dead letters block)
spine_freeze additionally requires: MSA checklist passes AND `paperproof verify`
  exits 0 (run internally by `freeze apply --level spine`)
language limits (allowed / forbidden) from the closure's records are unioned
  (deduplicated, sorted) into the FreezeItem
```

Freeze appends the FreezeItem itself, but setting `frozen=true` on graph records goes through a Committer batch commit — Freeze never writes graph files (docs/08 B8). `FreezeItem.evidence_ids` = the union of `evidence_bindings` over the closure's nodes (edges contribute none).

FreezeItem (`freeze/frozen_items.jsonl`):

```json
{
  "schema_version": "freeze_item.v1",
  "freeze_id": "FRZ-001",
  "project_id": "p4-ldi",
  "action": "freeze",
  "freeze_type": "local_freeze",
  "target_ids": ["NODE-001"],
  "evidence_ids": ["EU-001"],
  "allowed_language": ["…"],
  "forbidden_language": ["…"],
  "revokes": null,
  "created_at": "2026-07-07T00:00:00Z"
}
```

Unfreezing is an explicit **human** decision: `freeze unfreeze --target <id>` appends a FreezeItem with `action="unfreeze"` and `revokes=<FRZ-id>`, and triggers a Committer batch commit that sets `frozen=false` and re-opens the affected proofs (targets → `pending_proof`, re-proof items enqueued). A record is frozen iff its newest covering FreezeItem has `action="freeze"`.

## Compiler

The Compiler is the **only prose producer** in the system, and it runs in two phases.

### Phase 1: Dry Run (no prose)

`paperproof compiler dry-run` reads the frozen graph snapshot, maps it to a section plan, and reports readiness:

```json
{
  "schema_version": "compiler_dry_run.v1",
  "run_id": "CDR-001",
  "project_id": "p4-ldi",
  "snapshot_id": "GS-000012",
  "writing_ready": false,
  "section_plan": [
    {"section_id": "SEC-introduction", "role": "introduction", "nodes": ["NODE-Q", "NODE-T"]},
    {"section_id": "SEC-mechanism", "role": "mechanism", "nodes": ["NODE-001", "NODE-003"]}
  ],
  "gaps": [
    {"kind": "missing_evidence", "target_id": "NODE-005", "note": "empirical claim without binding"},
    {"kind": "unhandled_alternative", "target_id": "NODE-ALT-2", "note": ""}
  ]
}
```

Gap kinds (closed enum) and their mechanical triggers:

```text
missing_evidence        spine fact/mechanism node below the r3 evidence floor
                        (<2 bindings or <2 distinct documents — matches V-FRZ-02)
unhandled_alternative   alternative node not rejected and not parked(absorbed|not_needed)
weak_spine_edge         spine edge whose strength=conditional and whose assumptions
                        are not covered by any allowed_language in the closure
                        (v1 mechanical proxy: conditional spine edge with empty
                        language_limits — reported, human judges)
missing_section_claim   section-plan role with zero nodes assigned (pattern
                        template expects content there)
contract_violation      spine record whose scope fails the mechanical scope
                        compatibility check against the contract (docs/09 §0)
```

Rules:

```text
Gap identity is (kind, target_id). Every NEW gap spawns exactly one compile_queue
  item; re-running the dry run creates no duplicates, and gaps that no longer
  hold auto-complete their open items (op=cancel, detail=gap_resolved) [V-CDR-01].
The dry run must not create nodes, edges, or evidence [V-CDR-02].
The section plan covers every spine node exactly once [V-CDR-03].
writing_ready := gaps == [] AND a spine_freeze exists for the current snapshot.
Section plan topology follows the paper_type pattern from the PaperSpec.
```

Gap compile_queue items are Orchestrator TODOs: resolving them happens through the normal machinery (`docs request`, proofs, park, unfreeze+narrow), never by hand-editing.

**Reachability note (v1):** a first dry run after a clean spine freeze reports **zero gaps by construction** — V-FRZ-02 negates missing_evidence, MSA-5 negates unhandled_alternative, V-PR-13 negates the weak_spine_edge proxy, MSA-1 negates missing_section_claim, and commit-time V-NODE-03 plus contract immutability negate contract_violation. The gap machinery exists for re-runs after unfreeze/re-freeze cycles and for v1.1 contract re-opening; V-CDR tests exercise it by constructing degenerate fixture states directly (docs/11).

### Section plan template: `single_event_mechanism` (the v1 pattern)

Deterministic assignment — every spine node to exactly one section by `node_type`, ordered within a section by `(layer asc, node_id asc)`:

```text
SEC-introduction   question + thesis
SEC-concepts       definition nodes
SEC-mechanism      mechanism nodes
SEC-evidence       fact nodes
SEC-alternatives   no spine nodes; lists handled alternatives (rejected/parked)
                   as CONTEXT (their dispositions, not claims to re-argue)
SEC-conclusion     no nodes of its own; prose may restate thesis/limits using
                   annotations already present in the DraftMap
```

Empty sections (no nodes and no template expectation violated) are dropped from the plan; `SEC-introduction` empty would instead be `missing_section_claim` gaps (question/thesis are always expected).

### Phase 2: Draft Map and Prose

Only when `writing_ready` is true, `compiler draft-map` emits:

```json
{
  "schema_version": "draft_map.v1",
  "draft_map_id": "DRAFTMAP-001",
  "project_id": "p4-ldi",
  "based_on_dry_run": "CDR-002",
  "sections": [
    {
      "section_id": "SEC-mechanism",
      "role": "mechanism",
      "claims": [
        {
          "node_id": "NODE-001",
          "claim": "...",
          "evidence_ids": ["EU-001"],
          "allowed_language": ["..."],
          "forbidden_language": ["..."]
        }
      ],
      "edge_order": ["EDGE-001-002"]
    }
  ]
}
```

`edge_order` lists the spine edges whose both endpoints sit in this section, ordered `(source_node_id, target_node_id)` — the compile worker uses it to sequence argumentative moves. Claims appear in section-plan order. The DraftMap is fully derived: same dry run + same graph ⇒ byte-identical DraftMap.

Prose generation walks the DraftMap. `compiler draft-map` enqueues one compile_queue item per section (task_id `PROSE-<section_id>`); one CompileWorker per section claims it and writes **`agent_outputs/prose/<section_id>.md`** (workers never write `compiler/`); `paperproof compiler ingest-prose <file> --work-item <WI>` runs the V-PROSE rules as the item's validate-pass, copies the accepted file to `compiler/prose/<section_id>.md`, and commits the item — one command, two queue events (validate_pass + commit; the ingest-commit exception, docs/05). On V-PROSE failure it fails the item with the normal retry policy.

**Annotation grammar** (mechanical, checked by regexes in docs/09 §0):

```text
Every claim-bearing sentence carries "(claim: NODE-xxx)" inside the sentence.
Every citation carries "(cite: EU-xxx)" inside the SAME sentence as a claim
annotation, and the cited unit must be bound to one of that sentence's
annotated nodes in the DraftMap.
Transitions/signposting sentences carry no annotations.
Sentence boundaries: docs/09 §0.
```

The CompileWorker may choose wording, transitions, and paragraph structure — it may not add claims, strengthen claims beyond allowed_language, or cite anything outside the bound evidence (rules V-PROSE-01..04).

## Audit

Audit is the final check on the produced prose. It reports; it never rewrites. **In v1 the audit is fully mechanical (code only)**; the semantic AuditWorker pass (LLM judging whether a sentence exceeds `can_cite_for` in meaning rather than in string) is deferred to v1.1 — v1 relies on language-limit discipline plus these checks:

```text
binding    every (cite: EU-x) resolves; the EU is bound in the DraftMap to a
           node annotated in the same sentence; no cite outside a claim sentence
strength   no forbidden_language string (from the DraftMap section and the
           covering FreezeItems) appears in the prose (substring rules docs/09 §0)
scope      no contract forbidden_claims string appears verbatim in prose
           (best-effort literal check); every (claim: NODE-x) resolves to a
           frozen spine node
coverage   every DraftMap claim of each section is annotated at least once in
           that section; no (claim:)/(cite:) id absent from the DraftMap
```

AuditReport (`audit/audit_reports.jsonl`):

```json
{
  "schema_version": "audit_report.v1",
  "audit_id": "AUD-001",
  "project_id": "p4-ldi",
  "draft_ref": "DRAFTMAP-001",
  "findings": [
    {"kind": "strength", "location": "SEC-mechanism:para 2", "target_id": "NODE-001", "detail": "forbidden string present: …"}
  ],
  "passed": false
}
```

`kind` enum: `binding | strength | scope | coverage`. Every finding carries kind + location (`<section_id>:para N` or `:sentence N`) + target_id, so it can be routed as a compile_queue item mechanically [V-AUD-01] — fix the graph or re-compile the section; the loop closes without any hand-editing of state. Audit writes only `audit/`; prose files are untouched (hash-checked, V-AUD-02).
