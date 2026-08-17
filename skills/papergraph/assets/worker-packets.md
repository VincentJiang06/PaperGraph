# Worker packets

Every packet declares one task ID, bounded inputs, one output path, and prohibited
shared files. Returns are data for the Orchestrator to validate and merge.

## Cartographer

```text
Task: map the real field positions for <thesis> within <scope>.
Inputs: thesis and scope only.
Output: <task-output>/cartography.json with >=3 positions and one strongest objection.
Do not read the draft or optimize the map for its current argument.
```

## Advocate

```text
Task: steelman exactly <position_id>.
Inputs: thesis, scope, and that one position block.
Output: <task-output>/advocate-<position_id>.json with argument, best evidence,
concessions, and fair thesis response.
Do not edit paper.md or discuss another position.
```

## Adversary

```text
Task: construct the single strongest objection to <thesis>.
Inputs: thesis, scope, and validated position map.
Output: <task-output>/adversary.json with objection, success conditions, and evidence.
Do not merely negate the thesis or edit shared files.
```

## ClaimGrounder

```text
Task: ground exactly <claim_id>.
Inputs: claim text, kind, assigned raw/source references, and assigned output paths.
Output: one proposed claims.tsv row plus only the declared transform/metric/source.
Do not touch another claim ID, use network in a data transform, or edit claims.tsv.
```

## Held-out judges

EvalKeyBuilder receives only the thesis. Each EvalAdvocate receives the paper and
one answer-key position. EvalAdversary receives thesis, paper, and literature key.
ClaimAuditor extracts assertions independently before comparing the ledger. Each
Referee receives the paper and fixed rubric, but no gate result or peer judgment.
Each writes one disjoint JSON output. EvalAggregator validates all returns and
writes only the merged verdict.
