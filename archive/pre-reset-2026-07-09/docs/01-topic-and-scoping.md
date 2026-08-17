# 01 Topic Input and Scoping

This stage turns a loose research idea into a **fixed-scope research question with a declared outcome direction**. It is not the innovative part of the system, but everything downstream depends on it: the Logic Graph must argue one bounded question, not drift.

## Topic Input File

The user provides a single Markdown file describing the intended paper. For now this file is authored by hand (a customized "grill-me" interviewer may generate it later; user free-form input is out of scope until then). Tests use `examples/topic-input-p4.md`.

### Required sections

Nine sections, matched by heading **title text**:

```text
Topic             one-paragraph statement of the paper idea
Core Question     the single question the paper answers
Intended Thesis   the direction of the answer the author wants to argue
Paper Type        one of the supported paper patterns (see below)
Scope             what is inside: period, region, actors, mechanisms
Exclusions        hard exclusions — claims the paper must NOT make
Seed Claims       3-10 starting claims the author already believes matter
Known Sources     references / reports / notes the author already has
Success Criteria  what a finished argument must contain
```

### Parsing rules (deterministic; the parser is code, not judgment)

```text
P1  A section starts at any ATX heading (# through ######) whose trimmed text
    case-insensitively equals a required section title. Heading LEVEL is ignored
    (the example file uses # everywhere; that is valid).
P2  A section's body runs to the next recognized heading or EOF.
P3  Section order is free. A duplicated recognized heading fails V-SPEC-01
    (ambiguous). An unrecognized heading and its body are ignored with a warning.
P4  A section is "empty" if its body is whitespace-only after stripping.
P5  List items are lines starting with "-", "*", or "N." / "N)" (numbering
    stripped). A list-valued section whose body contains no list items yields
    its whole body as one item; stray non-list lines mixed BETWEEN list items
    are ignored with a warning.
P6  Scope items of the form "Key: value" with Key case-insensitively in
    {Period, Region, Actors, Mechanisms} populate the structured scope; Actors
    and Mechanisms values split on "," (trimmed). Non-matching scope lines are
    carried verbatim into the contract's in_scope list only.
P7  Text is treated as UTF-8; CJK content is legal everywhere (counting rules:
    docs/09 §0).
```

Supported paper patterns (affects BFS topology and compiler section plan, never bypasses Proof/Commit):

```text
single_event_mechanism            (the only pattern implemented in v1)
parallel_case_bfs_then_merge
core_experiment_empirical
literature_debate_mapping
policy_design_memo
freeform_research_design
```

## Scoping Stage

Scoping is run in the main Claude Code session (Orchestrator), but the artifact generation is **code**: `paperproof spec build <topic-file>` parses deterministically and emits both artifacts below. The interactive part is the human reviewing the drafts; requested changes are applied by re-running `spec build` with `--patch <json-file>`. The patch file has exactly two optional top-level keys, each an RFC 7386 merge patch:

```json
{"paper_spec": {"scope": {"period": "2021-2023"}}, "project_contract": {"forbidden_claims": ["..."]}}
```

Application order is fixed: (1) parse topic file → PaperSpec; (2) apply `paper_spec` patch; (3) derive the contract **from the patched spec**; (4) apply `project_contract` patch; (5) write both. So a spec-level change propagates into the contract automatically, and a contract-level patch wins last. Nobody hand-edits `specs/` files.

### PaperSpec (`specs/paper_spec.json`)

Machine-readable restatement of the topic input. Derivation is fixed:

| PaperSpec field | derived from |
| --- | --- |
| `project_id` | CLI argument (`--project`), slug `[a-z0-9-]{3,32}` |
| `paper_type` | Paper Type section, verbatim token |
| `core_question` | Core Question body, verbatim |
| `intended_thesis` | Intended Thesis body, verbatim |
| `scope` | structured keys from Scope (rule P6) |
| `hard_exclusions` | Exclusions list items, verbatim |
| `seed_claims` | Seed Claims list items, verbatim (numbering stripped) |
| `known_sources` | Known Sources list items, verbatim |
| `success_criteria` | Success Criteria list items, verbatim |
| `bfs_plan` | fixed template per paper_type (below) |
| `source_files` | `[]` at build time; grows via `paperproof docs ingest` |

```json
{
  "schema_version": "paper_spec.v1",
  "project_id": "p4-ldi",
  "paper_type": "single_event_mechanism",
  "core_question": "Why can pension de-risking transform solvency risk into liquidity risk?",
  "intended_thesis": "De-risking via LDI reduces funding volatility but concentrates liquidity fragility.",
  "scope": {
    "period": "2020-2023",
    "region": "UK",
    "actors": ["DB pension funds", "LDI managers", "gilt market"],
    "mechanisms": ["leverage", "collateral calls", "fire sales"]
  },
  "hard_exclusions": ["no generalization to all mature markets without qualifiers"],
  "seed_claims": ["..."],
  "known_sources": ["Bank of England Financial Stability Report, November 2022"],
  "success_criteria": ["..."],
  "bfs_plan": [
    {"bfs_id": "BFS-MAIN", "purpose": "core mechanism chain", "depends_on": []},
    {"bfs_id": "BFS-ALT", "purpose": "alternative explanations", "depends_on": ["BFS-MAIN"]}
  ],
  "source_files": []
}
```

`bfs_plan` must be a DAG. v1 knows one template: `single_event_mechanism` ⇒ exactly the two lanes above. Other patterns get templates when they get implemented (v2).

### ProjectContract (`specs/project_contract.json`)

The binding agreement every later stage checks against:

```json
{
  "schema_version": "project_contract.v1",
  "project_id": "p4-ldi",
  "contract_version": 1,
  "fixed_question": "verbatim core_question",
  "outcome_direction": "verbatim intended_thesis",
  "scope": {"period": "2020-2023", "region": "UK", "actors": ["..."], "mechanisms": ["..."]},
  "in_scope": ["every Scope list item, verbatim"],
  "out_of_scope": [],
  "forbidden_claims": ["every Exclusions item, verbatim"],
  "success_criteria": ["..."],
  "accepted_by_user": false,
  "accepted_at": null
}
```

Derivation: `fixed_question` = core_question; `outcome_direction` = intended_thesis; `scope` = structured spec scope (this copy is what mechanical scope checks use — V-NODE-03, docs/09 §0); `in_scope` = all Scope items verbatim (human/worker-readable); `out_of_scope` = `[]` in v1 (the structured scope is the boundary authority); `forbidden_claims` = hard_exclusions.

`in_scope` is the raw topic's Scope lines **verbatim**, not a render of the structured scope. A `paper_spec.scope` patch (period/region/actors/mechanisms) updates the machine-authoritative STRUCTURED `scope` — the V-NODE-03 authority — but does NOT rewrite the human-readable `in_scope` list; to keep the two in step, patch `project_contract.in_scope` separately in the same patch file.

Rules (binding contract: docs/08 B1–B2; checks: V-SPEC, V-GATE-01 in docs/09):

```text
`spec accept` is the only way to set accepted_by_user=true (+ accepted_at); it
  requires explicit human confirmation in the session.
The contract is immutable after acceptance: `spec build` refuses to overwrite an
  accepted contract. Changing it bumps contract_version, archives the old file to
  specs/history/project_contract.v<N>.json, and re-opens affected proofs
  (v1: manual re-open, docs/10 §1).
Every LogicNode must fit the contract scope; Proof marks out_of_scope records
  rather than silently dropping them.
forbidden_claims feed directly into Proof's scope_check and the final Audit.
The Orchestrator must get explicit user confirmation before graph expansion
  starts — no expansion, proof task, or worker dispatch may run while the latest
  contract has accepted_by_user=false  [V-GATE-01].
After acceptance the LAYER-0 EXPANSION commits first, THEN the EVIDENCE
  SEEDING sweep runs (r3/v2.1 D4-D5, docs/04): ingest every locally available
  Known Source, then per fact/mechanism layer-0 node one fanned request + wave
  (`docs request --target N ... --fan` → `docs wave --request DR-x --fan`)
  until the V-SWEEP-01 floor — proofs never start against an empty evidence base.
```

## Why This Stage Exists

Without a fixed contract, BFS expansion has no stopping criterion and Proof has no scope to check against. The contract gives:

1. A **fixed scope** — Proof can reject out-of-scope expansion instead of arguing about it.
2. A **declared outcome direction** — the graph grows toward a thesis, not in all directions.
3. A **user-owned decision record** — the human accepts the research scope; agents never widen it on their own.
