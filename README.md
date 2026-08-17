# PaperGraph

PaperGraph is a small, coding-agent-supervised workflow that turns a research topic into a
finished Markdown paper. It improves two failure modes with re-runnable checks:

- **Divergence:** the paper must engage the field's real positions and its strongest objection.
- **Rigor and traceability:** every empirical claim must reproduce from raw data or verify against
  a saved source.

The project deliberately does not provide a claim graph, queue framework, model API wrapper,
database, or product CLI. The host coding agent coordinates native subagents; PaperGraph itself
does not need a model API key.

## Current state

The project was reset on 2026-07-09 after the previous graph/CLI designs failed to improve paper
quality reliably. That implementation is retained only under `archive/pre-reset-2026-07-09/` and
is not an implementation source.

The active workflow is experimental but runnable:

- Four domain runs under `runs/` pass both author-facing gates.
- The independent eval has literature answer keys for all four runs.
- Only `nuclear-safety` currently has the complete D2/D3/D4b/D5 judgment panel; it is `REVISE`.
- The other runs have only partial evals. A mechanical `SHIP` result without a complete panel is
  provisional and must not be treated as a release decision.
- The required gated-versus-freehand A/B baseline has not been completed.

Known executable conformance gaps, intentionally not fixed during documentation-only work:

- `eval/harness.py` does not yet fail closed when judgment fields are absent. It also does not
  fully enforce the steelman mean, honesty-flag, and referee-band rules in `eval/EVAL.md`.
- `gates/rigor_gate.py` reports a failed DVC reproduction, but its final exit decision currently
  depends only on values found in metric files; stale metrics could therefore mask a DVC failure.
- `eval/protocol.md` does not yet define every per-judge output and aggregation field consumed by
  the demonstrated verdict artifact. That interface must be completed on the eval track.
- `eval/selftest.py` passes its present cases but has no negative case proving that a missing panel
  cannot produce `SHIP`.

## Document map

The documents are intentionally split by responsibility:

| Layer | Canonical files | Purpose |
|---|---|---|
| Design | `DESIGN.md` | Product goal, trade-offs, and the small-system architecture |
| Workflow | `WORKFLOW.md` | Topic-to-paper loop, agent roles, parallel waves, and stop conditions |
| Gate interfaces | `gates/divergence.md`, `gates/rigor.md` | Exact author-side file formats and deterministic pass rules |
| Held-out eval | `eval/EVAL.md` | Independent quality policy and final ship criteria |
| Eval interface | `eval/protocol.md` | Agent inputs, output contract, and aggregation handoff |
| History | `CHANGELOG.md`, `eval/CHANGELOG.md` | Separate workflow and eval change tracks |

`AGENTS.md` is the cross-agent operating contract. `CLAUDE.md` is the Claude Code supplement.
`archive/` is historical evidence only, and `product/` is product planning; neither is binding.

When documents disagree, the narrowest boundary document wins: gate file questions go to the
matching `gates/*.md`; held-out verdict questions go to `eval/EVAL.md`; orchestration questions go
to `WORKFLOW.md`; design intent goes to `DESIGN.md`. Executable scripts must be brought into
conformance with these documents rather than silently redefining them.

## Quality model

```text
topic
  -> native subagents map positions, steelman, attack, and ground evidence
  -> orchestrator owns and revises paper.md
  -> both in-loop gates PASS                    candidate paper
  -> held-out eval re-derives the yardstick     SHIP or REVISE
```

The two layers solve different problems:

- `gates/` is a fast, deterministic floor used during every revision. It is useful but gameable
  because the author also creates `positions.md` and `claims.tsv`.
- `eval/` is an out-of-loop, author-blind judge. It derives its position map from real literature,
  dispatches independent judgment agents, and is required for a final `SHIP` decision.

Passing both gates produces a candidate, not a finished release. Missing eval dimensions fail
closed: the result is incomplete, never `SHIP`.

## Per-paper files

```text
runs/<slug>/
  paper.md          artifact revised by the orchestrator
  positions.md      author-side map used by the divergence gate
  claims.tsv        empirical-claim ledger used by the rigor gate
  transforms/       one deterministic transform per data claim
  metrics/          transform outputs checked by the rigor gate
  sources/          saved text for source claims
  dvc.yaml          data-claim pipeline; omitted when there are no data claims
  dvc.lock          generated provenance for data claims
  gate_report.md    latest results from both in-loop gates
```

The exact `positions.md` and `claims.tsv` contracts live in the two gate interface documents.

## Run the checks

From the repository root:

```bash
python3 gates/rigor_gate.py runs/<slug>
python3 gates/divergence_gate.py runs/<slug>
```

For a pre-ship held-out evaluation, first create the literature answer key and judgment panel by
following `eval/protocol.md`, then run:

```bash
python3 eval/harness.py score runs/<slug> \
  --key eval/corpus/<slug>/answer_key.json \
  --arm gated
python3 eval/selftest.py
```

Data claims require DVC because the rigor gate delegates re-execution and provenance to it.
Source-only papers do not need a DVC pipeline.

## Agent execution

Use the host coding agent's native subagent framework. Do not add provider SDKs or API-key
configuration to PaperGraph. Parallel work is expected, but shared files have one writer:

- advocates run in parallel, one bounded task per mapped position;
- the adversary runs alongside the advocates;
- claim grounders run in parallel with disjoint `claim_id` outputs;
- held-out advocates, adversary, claim auditor, and at least three referees run independently;
- only the orchestrator merges worker returns into shared paper artifacts.

The full dispatch and ownership rules are in `WORKFLOW.md` and `AGENTS.md`.

## Non-negotiables

- Never use archived framework files as current guidance.
- Never invent a source, quote, number, or provenance record.
- Never weaken a gate or the eval to admit a failing paper.
- Never call an in-loop gate result an independent quality verdict.
- Never ship while any held-out eval dimension is missing or failing.
- Keep workflow and eval changes on their separate documented tracks.
