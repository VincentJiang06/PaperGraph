# Workflow

## Authority and state

The active product is the small file-based topic-to-paper loop described by the
repository's `DESIGN.md`, `WORKFLOW.md`, gate contracts, and eval contracts. Do
not restore archived claim graphs, queues, databases, WebUI, `paperproof`, or
`nd`. Durable state is validated files, never chat.

The Orchestrator owns scope, dispatch, merging, revision, and stop decisions. It
is the only writer of `paper.md`, `positions.md`, and `claims.tsv`. Gate scripts
alone update `gate_report.md`; the EvalAggregator alone writes the merged held-out
verdict.

## Run shape

1. Create `runs/<slug>/` and scope one thesis question. Put exactly one
   `field-weight: humanities|mixed|science` line at the top of `paper.md`; record
   in/out boundaries and evidence that would narrow or overturn the thesis.
2. Give one Cartographer only the thesis and scope. Validate at least three
   genuinely disagreeing positions and exactly one strongest objection before
   the Orchestrator writes `positions.md`.
3. Dispatch all Advocates and the Adversary concurrently. Each Advocate receives
   exactly one position. The Adversary receives the thesis, scope, and map, and
   returns one strongest objection rather than generic criticism.
4. Identify every load-bearing empirical assertion. Allocate stable, disjoint
   claim IDs. Dispatch all ClaimGrounders concurrently; data claims own one
   transform and metric path, while source claims own one archived text path.
5. Validate returns and merge. Draft `paper.md` only after the position and claim
   evidence exists. Cite claim IDs in empirical sentences and tag real position
   engagement according to the repository divergence contract.
6. Run both author gates. Revise only the responsible author artifact and repeat
   until both pass. Preserve gate thresholds and field map.
7. Freeze a candidate and start a blind held-out wave. Do not expose author
   `positions.md`, gate results, or other judges where the eval protocol forbids
   them. Aggregate only after every required output validates.

## Parallel ownership

```text
scope -> Cartographer -> orchestrator merge
      -> [Advocate P1 | Advocate P2 | ... | Adversary] -> merge
      -> [Grounder C1 | Grounder C2 | ...]             -> merge
      -> draft -> [divergence gate | rigor gate]
      -> [EvalAdvocates | EvalAdversary | ClaimAuditor | Referee x3+] -> aggregator
```

Every worker packet declares bounded inputs, one task ID, and one output path.
Concurrent tasks must have disjoint IDs and paths. Workers never edit shared
artifacts. Reject a return that adds undeclared scope, lacks required fields, or
contains unverifiable citations.

## Stop conditions

- Stop author revision only when both author gates pass.
- Treat a dual gate pass as candidate, never `SHIP`.
- Stop held-out evaluation only after all D1-D5 inputs and all required referee
  returns exist.
- Return `SHIP` only when `validate_eval_bundle.py` reports `SHIP`; missing data,
  unresolved honesty flags, weak objection handling, or referee failure means
  `INCOMPLETE` or `REVISE`.
- If a gated paper does not outperform its freehand baseline on the independent
  scorecard, report that result; do not add framework to obscure it.
