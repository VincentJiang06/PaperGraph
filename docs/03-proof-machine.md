# 03 Proof Machine

The Proof Machine atomically resolves single logical questions. Its determinism principle:

```text
The worker NEVER chooses a verdict. It fills a fixed check form with discrete
answers. Code computes the verdict from the form via a published decision table.
Claude answers atomic questions; code decides.
```

This removes the largest source of nondeterminism (verdict selection), makes every proof reproducible from its form, and makes validation mechanical.

## Task Types

```text
NODE_CHECK   Is claim A well-formed, in scope, and grounded?
EDGE_CHECK   Does A actually sustain B, as the edge_claim states?
```

(`BINDING_CHECK` — does evidence E support claim A at the cited location — is deferred to v1.1; v1 covers binding quality via EvidenceUnit citation boundaries plus the final Audit.)

**Ordering rule:** an EDGE_CHECK is enqueued only when both endpoint nodes are `active`. Edge workers therefore never re-litigate node truth — they assess only the inference. This ordering is enforced by the queue (`blocked_by` the endpoint NODE_CHECK items; the queue engine keeps an EDGE_CHECK unclaimable until both endpoints are active — docs/05) and is itself a determinism device.

## ProofTask

Created by code from queue items:

```json
{
  "schema_version": "proof_task.v1",
  "task_id": "PT-EDGE-001-002",
  "project_id": "p4-ldi",
  "task_type": "EDGE_CHECK",
  "target": {"edge_id": "EDGE-001-002", "source_node_id": "NODE-001", "target_node_id": "NODE-002"},
  "context_pack": "proof/context/CTX-EDGE-001-002.json",
  "docs_pack": "docs/docspacks/DOCSPACK-EDGE-001-002.json",
  "output_file": "agent_outputs/proof_results/PT-EDGE-001-002.proof_result.json"
}
```

For a NODE_CHECK, `target` is `{"node_id": "NODE-001"}` and `task_id` is `PT-NODE-001`. Any **subsequent bundle for the same target** — a staleness rebuild or a re-proof after a needs_repair/needs_docs verdict — appends a revision suffix to all four ids/paths: `PT-NODE-001-r2`, `CTX-...-r2`, `DOCSPACK-...-r2`, `...-r2.proof_result.json` (per-target counter). A Committer-created re-proof work item is a NEW work item with `task_id=null` and `bundle=null` until `proof build-tasks` mints the next revision. Bundle files are immutable once written; a rebuild writes new files rather than overwriting (the verdict record keeps the exact bundle paths it was judged against, so `trace` stays honest).

ContextPack and DocsPack schemas: `docs/08` B4. The bundle is self-contained; the worker reads nothing else. The ContextPack includes a `claim_digest` — `{node_id, claim}` for every non-rejected node in the project — which is what makes `duplicate_check` answerable beyond 1-hop neighbors (v1 graphs are small; this stays cheap).

## The Check Form

The worker's entire output is one file containing the form plus conditional attachments. Every form field is a closed enum.

```json
{
  "schema_version": "proof_result.v1",
  "task_id": "PT-EDGE-001-002",
  "project_id": "p4-ldi",
  "target_type": "edge",
  "target_id": "EDGE-001-002",
  "form": {
    "scope_check": "in_scope",
    "duplicate_check": {"duplicate": false, "duplicate_of": null},
    "wellformed_check": "single_proposition",
    "evidence_check": "sufficient",
    "inference_check": "holds_only_with_assumptions"
  },
  "assumptions": ["Gilt yield moves were rapid enough to outpace collateral buffers."],
  "evidence_used": ["EU-001"],
  "language_limits": {
    "allowed": ["In the 2022 UK episode, de-risking via leveraged LDI transmitted rate moves into liquidity demand."],
    "forbidden": ["De-risking always creates liquidity crises."]
  },
  "repair_proposals": [],
  "docs_requests": [],
  "notes": "≤150 words of reasoning summary."
}
```

There is no `verdict` field and no **worker-invented id**: the form carries only ids handed to it in its inputs (`task_id`, `target_id`, `duplicate_of`, evidence ids) — it must not contain a `proof_result_id` or any id-valued field beyond the schema's own (V-PR-03). The PR- id is assigned by the Validator when it appends the verdict record; the verdict is computed at validation time and recorded alongside the form in `proof/proof_results.jsonl` (schema below).

Form fields and their closed enums:

```text
scope_check       in_scope | out_of_scope
                  (against ContextPack contract_scope + forbidden_claims)
duplicate_check   {duplicate: false, duplicate_of: null}
                  | {duplicate: true, duplicate_of: <non-rejected id from ContextPack>}
wellformed_check  single_proposition | too_broad | compound | not_evaluated
evidence_check    not_required | sufficient | insufficient | contradicting | not_evaluated
inference_check   holds | holds_only_with_assumptions | gap | fails | not_evaluated
                  (EDGE_CHECK only; the field is ABSENT on NODE_CHECK forms —
                   present-on-node or absent-on-edge is a schema violation [V-PR-04])
```

For a `question` node, "single proposition" reads as "single well-posed question". `wellformed_check` judges the target's own text: the node `claim` for NODE_CHECK, the `edge_claim` for EDGE_CHECK.

## The Evaluation Ladder

`not_evaluated` is a sentinel, not a judgment: it means "an earlier stage already decided this record's fate, so this question was never posed". The ladder below is the **only** legal shape of a form. It exists because later questions are ill-posed once an earlier stage fails (you cannot evidence-check a compound claim, and there is nothing to infer over insufficient evidence) — and because it gives workers a deterministic stopping rule instead of "fill remaining fields conservatively".

```text
Stage A  (always answered)
         scope_check, duplicate_check.
         If scope_check=out_of_scope OR duplicate=true:
             wellformed_check = evidence_check = inference_check = not_evaluated. STOP.

Stage B  wellformed_check.
         If too_broad | compound:
             attach exactly one narrow repair;
             evidence_check = inference_check = not_evaluated. STOP.

Stage C  evidence_check.
         fact and mechanism NODES may not answer not_required [V-PR-05];
         all other targets (including every edge) may.
         If insufficient:  attach ≥1 docs_requests; inference_check = not_evaluated. STOP.
         If contradicting: evidence_used non-empty;   inference_check = not_evaluated. STOP.

Stage D  (EDGE_CHECK only) inference_check.
         gap  ⇒ attach 1–2 bridge repairs.
         holds_only_with_assumptions ⇒ assumptions non-empty.
         holds ⇒ assumptions empty.
```

Ladder-shape enforcement is mechanical [V-PR-14]: a field is `not_evaluated` **iff** an earlier stage stopped the ladder. A form with `wellformed_check=not_evaluated` but `scope_check=in_scope, duplicate=false` is invalid; so is `evidence_check=sufficient` after `wellformed_check=too_broad`.

Attachment rules (apply only to evaluated stages; everything an unevaluated stage would attach must be empty/null):

```text
evidence_check=sufficient|contradicting  ⇒ evidence_used ≥1 (ids from DocsPack only)
evidence_check=insufficient              ⇒ docs_requests ≥1 (need + search_hints each);
                                           partial evidence_used allowed (may be empty)
evidence_check=not_required|not_evaluated⇒ evidence_used = []
inference_check=gap                      ⇒ 1–2 repair_proposals, all kind=bridge
wellformed_check=too_broad|compound      ⇒ exactly 1 repair_proposal, kind=narrow
otherwise                                ⇒ repair_proposals = []
EDGE_CHECK: assumptions non-empty  iff inference_check=holds_only_with_assumptions [V-PR-15]
NODE_CHECK: assumptions allowed (possibly empty) only when evidence_check ∈
            {not_required, sufficient}; otherwise assumptions = []
computed verdict = pass                  ⇒ language_limits.allowed AND .forbidden non-empty
computed verdict ≠ pass                  ⇒ language_limits = null  [V-PR-13]
```

Repair proposals (the only two kinds):

```json
{"kind": "bridge", "claim": "Solvency risk and liquidity risk are distinct categories.", "node_type": "definition"}
{"kind": "narrow", "narrowed_claim": "UK DB pension funds using leveraged LDI faced margin calls in Sept 2022."}
```

A bridge proposes a missing **co-premise** (edge gaps only): a claim that must hold for the inference A→B to go through. `node_type` ∈ `fact | mechanism | definition | alternative` (never `question`/`thesis`). The worker proposes only the claim; the **Committer** wires it into the graph — bridge node X plus edge X→B (`depends_on` for definitions, `supports` otherwise) — so that a proven bridge appears in the re-proof's ContextPack and joins the spine (exact wiring: docs/08 B6). A narrow proposes replacement text for an overbroad/compound claim — same record id, new claim version, re-proved from scratch. Workers never propose ids, edges, or nested structures.

## The Decision Table

Code computes the verdict by walking this table top-down; **first match wins**. The table is aligned with the ladder (a stage that stopped the ladder is always the first match), it is total over ladder-valid forms, and the precedence order is part of the contract — changing it is a schema change.

| # | condition | computed verdict |
| --- | --- | --- |
| 1 | scope_check = out_of_scope | rejected (out_of_scope) |
| 2 | duplicate_check.duplicate = true | rejected (duplicate) |
| 3 | wellformed_check ∈ {too_broad, compound} | needs_repair (narrow) |
| 4 | evidence_check = contradicting | rejected (contradicted) |
| 5 | evidence_check = insufficient | needs_docs |
| 6 | inference_check = fails | rejected (contradicted) |
| 7 | inference_check = gap | needs_repair (bridge) |
| 8 | otherwise | pass — strength = **conditional** if `assumptions` non-empty, else **strong** |

Row 8's "otherwise" is exactly: `wellformed=single_proposition`, `evidence ∈ {not_required, sufficient}`, and (edges) `inference ∈ {holds, holds_only_with_assumptions}`. The strength rule is uniform for nodes and edges: recorded assumptions make a pass conditional. For edges [V-PR-15] ties assumptions to `holds_only_with_assumptions`; for nodes, assumptions express "the evidence carries this claim only under these conditions".

Verdict space — 4 values with reason subfields:

```text
pass         (strength: strong | conditional)
needs_repair (repair_kind: bridge | narrow)
needs_docs
rejected     (reason: contradicted | out_of_scope | duplicate)
```

Because the table is total and deterministic over ladder-valid forms, the same form always yields the same verdict; golden tests enumerate every reachable row and a fuzz test proves totality (`docs/11` §6).

## The Verdict Record

The Validator appends the computed result to `proof/proof_results.jsonl`:

```json
{
  "schema_version": "verdict_record.v1",
  "proof_result_id": "PR-001",
  "project_id": "p4-ldi",
  "work_item_id": "WI-000002",
  "task_id": "PT-EDGE-001-002",
  "target_type": "edge",
  "target_id": "EDGE-001-002",
  "form": { "…": "verbatim copy of the validated form" },
  "assumptions": [], "evidence_used": [], "language_limits": null,
  "repair_proposals": [], "docs_requests": [], "notes": "…",
  "computed_verdict": {"verdict": "needs_repair", "repair_kind": "bridge", "strength": null, "reason": null},
  "bundle": {
    "task_file": "proof/tasks/PT-EDGE-001-002.json",
    "context_pack": "proof/context/CTX-EDGE-001-002.json",
    "docs_pack": "docs/docspacks/DOCSPACK-EDGE-001-002.json"
  },
  "validated_at": "2026-07-07T00:00:00Z"
}
```

`computed_verdict` uses exactly one populated subfield: `strength` iff pass, `repair_kind` iff needs_repair, `reason` iff rejected, all null for needs_docs. V-PR-12 recomputes the table on every `verify` run; a mismatch is state corruption (exit 3).

## Validation

The Validator (deterministic code, no LLM) checks the form's internal consistency — the V-PR rules in `docs/09`. The most important:

```text
form completeness matches task_type (inference_check field iff EDGE_CHECK)  [V-PR-04]
fact/mechanism NODES may not answer evidence not_required                   [V-PR-05]
evidence_used ⊆ DocsPack                                                    [V-PR-06]
conditional attachments present exactly when required                       [V-PR-07]
no verdict field; no id fields; no numeric-valued JSON fields               [V-PR-03, 08]
ladder shape: not_evaluated exactly where an earlier stage stopped          [V-PR-14]
edge assumptions iff holds_only_with_assumptions                            [V-PR-15]
pass verdicts require language_limits.allowed AND .forbidden                [V-PR-13]
```

Failure ⇒ work item `failed` with rule IDs; ≤2 retries with the violated rules appended to the prompt (the retry overwrites the same declared output file); then dead letter.

## Worker Protocol

A ProofWorker is a Claude subagent whose entire contract is:

```text
1. Read the ProofTask, ContextPack, DocsPack. Nothing else in the project.
2. Walk the evaluation ladder in order; stop where the ladder stops; fill
   every remaining field with not_evaluated exactly as the ladder dictates.
3. Write the one output file, schema-valid. Stop. Chat text is discarded.
```

Hard prohibitions:

```text
Do not choose or write a verdict — there is no field for it.
Do not write essay prose; notes ≤ 150 words (word count: docs/09 §0).
Do not modify any file other than output_file.
Do not use evidence outside the DocsPack; missing evidence ⇒
  evidence_check=insufficient + docs_requests.
Do not invent citations.
Do not propose more than two bridges; never expand bridges recursively.
Do not use numeric scores; the form has no numeric-valued field at all.
```

If a worker needs literature the DocsPack lacks, it does **not** search — `evidence_check=insufficient` routes a DocsRequest to the Docs pipeline (`docs/04`), keeping proof atomic and search memoized.

## After the Worker

```text
Validator  checks V-PR rules, computes the verdict from the form, appends the
           verdict record to proof/proof_results.jsonl (PR- id assigned here),
           moves the work item validating → validated.
Committer  applies the verdict→action table (docs/08 B6): lifecycle and strength
           updates, bridge candidates, claim-narrowing versions, DocsRequests,
           tombstones — all in one CommitDecision.
```

Workers never do either. Queue mechanics: `docs/05`; boundary contract: `docs/08` B5–B6.

## Worked Ladder Examples

```text
Out-of-scope fact node:
  scope=out_of_scope; duplicate answered (false); wellformed/evidence = not_evaluated;
  no attachments; verdict rejected(out_of_scope).
  (Under the pre-r2 table this case was unfillable: every legal evidence answer
   forced an attachment that made no sense. The ladder exists for this reason.)

Compound claim with suspicious evidence:
  wellformed=compound stops the ladder ⇒ needs_repair(narrow). Contradiction, if
  real, is caught when the narrowed claim is re-proved — you cannot meaningfully
  evidence-check a claim that is really two claims.

Edge over solid endpoints, missing middle step:
  A/D stages pass, evidence not_required, inference=gap ⇒ 1–2 bridge proposals
  ⇒ needs_repair(bridge); Committer creates bridge candidates and blocks the
  edge's re-proof on them.
```
