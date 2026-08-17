# Agent Protocol

## Current scope

This repository is in **documentation-only mode** unless the user explicitly asks to implement or
change executable behavior. Documentation work may inspect and test existing scripts, but it must
not edit Python, data, generated reports, or run artifacts.

The active PaperGraph is a small topic-to-paper workflow. Do not restore the archived Logic Graph,
`paperproof`/`nd` CLIs, schemas, queues, database, WebUI, or worker framework.

## Read order and authority

1. `DESIGN.md` - goals, boundaries, and why the system is deliberately small.
2. `WORKFLOW.md` - the orchestrator loop, parallel waves, and artifact ownership.
3. `gates/divergence.md` and `gates/rigor.md` - exact in-loop file and verdict contracts.
4. `eval/EVAL.md` - held-out evaluation policy and final ship criteria.
5. `eval/protocol.md` - independent-agent inputs and output handoff.

For a boundary conflict, the narrowest contract wins. Gate interfaces win for gate files; `EVAL.md`
wins for release verdicts; `WORKFLOW.md` wins for orchestration. `archive/` and `product/` are never
implementation authority.

## Roles

```text
Orchestrator       owns scope, shared artifacts, dispatch, merges, revisions, and stop decisions
Cartographer       maps the author-side field positions; returns one bounded map
Advocate           steelmans exactly one mapped position
Adversary          constructs the strongest objection to the working thesis
ClaimGrounder      grounds exactly one empirical claim in a transform or saved source
EvalKeyBuilder     derives an answer key from real literature, blind to author scaffolding
EvalAdvocate       scores exactly one answer-key position, blind to other judges
EvalAdversary      searches for a stronger unaddressed objection
ClaimAuditor       extracts empirical assertions independently of claims.tsv
Referee            one blind rubric judgment; at least three run independently
EvalAggregator     validates completeness and merges judge outputs; does not author judgments
```

All model work uses the host coding agent's native subagents. The project must not require an API
key, provider SDK, or hidden network model call.

## Parallelism and ownership

Parallelism is the default whenever tasks are independent:

1. After cartography, dispatch one Advocate per position plus one Adversary concurrently.
2. After the empirical claims are identified, dispatch one ClaimGrounder per `claim_id`
   concurrently.
3. At held-out eval, dispatch all EvalAdvocates, the EvalAdversary, ClaimAuditor, and at least three
   Referees concurrently. Aggregate only after every required return exists.

Workers receive bounded inputs and never edit shared artifacts. Only the Orchestrator writes
`paper.md`, `positions.md`, and `claims.tsv`. Gate scripts alone update `gate_report.md`.
ClaimGrounders may write only their assigned `transforms/<claim_id>.py`,
`metrics/<claim_id>.json`, or `sources/<claim_id>.txt` when explicitly authorized; claim IDs and
paths must be disjoint. Eval judges write only their assigned output, and the EvalAggregator alone
writes the merged verdict file.

Chat text is not durable state. The orchestrator must validate each worker return against the
relevant interface before merging it.

## Quality and release rules

- Both author-facing gates run on every paper and every candidate must pass both.
- Gate success means **candidate**, not `SHIP`.
- Held-out eval agents must be blind to `positions.md`, gate results, and one another wherever the
  eval protocol says so.
- A final `SHIP` requires every D1-D5 input and every required referee return. Missing dimensions
  are incomplete and fail closed, regardless of what the current harness prints.
- Never edit an answer key, threshold, gate, or eval rubric to make a paper pass.
- Workflow changes and eval changes use separate changelogs and must not be bundled as one quality
  adjustment.

## Change discipline

- Keep edits small and consistent with the current file-based design.
- A file-format or pass-rule change must update its matching interface document in the same change.
- A workflow change belongs in `CHANGELOG.md`; an eval change belongs in `eval/CHANGELOG.md`.
- Do not manually edit generated `gate_report.md`, `eval/reports/`, or `eval/scoreboard.tsv`.
- Do not commit or push unless the user explicitly asks. Push only to
  `github.com/VincentJiang06/PaperGraph`, never to a company GitLab.
