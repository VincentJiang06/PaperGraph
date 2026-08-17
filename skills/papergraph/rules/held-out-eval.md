# Held-out evaluation

The held-out panel judges a frozen candidate independently of author scaffolding.
Both author gates must already pass, but their results are not evidence for this
panel.

## Blind wave

1. EvalKeyBuilder receives the thesis only and derives D1 positions from fetched
   literature. Every position resolves to a real archived/fetched source.
2. Dispatch one EvalAdvocate per D1 position, one EvalAdversary, one ClaimAuditor,
   and at least three Referees concurrently. Judges do not see one another. Where
   the repository eval protocol requires blindness, do not expose author
   `positions.md`, author gate results, or author-selected claims.
3. Validate each bounded return before saving it. The EvalAggregator authors no
   judgment; it checks completeness and invokes the deterministic bundle validator.

## Bundle contract

The validator expects exactly these dimensions:

| File | Required release evidence |
|---|---|
| `d1_answer_key.json` | Nonempty, uniquely identified literature positions. |
| `d2_steelmans.json` | One passing steelman judgment for every D1 position. |
| `d3_adversary.json` | Objection robustness `PASS`; no stronger unaddressed objection. |
| `d4b_claim_audit.json` | Claims complete, traceability 1.0, no honesty flags. |
| `d5_referees.json` | Three or more unique independent referees in the passing band. |

Missing or malformed files produce `INCOMPLETE`. Complete evidence that misses a
quality condition produces `REVISE`. Only a complete conforming bundle produces
`SHIP`. Never edit the answer key, rubric, threshold, or validator to admit a
specific candidate.

After `REVISE`, change the paper or author workflow, rerun both author gates, and
evaluate a new frozen candidate. Workflow and eval rule changes remain separate
lifecycle tracks.
