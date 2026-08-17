# Claude Code Instructions

Follow `AGENTS.md` first. This file adds only Claude-specific operating rules.

## Active direction

PaperGraph is a deliberately small, file-based topic-to-paper workflow. The old Logic Graph,
`paperproof`/`nd` CLIs, schemas, queues, database, and WebUI are archived failed attempts. Never
read `archive/**` as guidance and never resurrect those components.

The current repository mode is documentation-only unless the user explicitly requests executable
implementation. Do not edit Python, data, generated reports, or run artifacts during documentation
work.

## Native subagents

Use Claude Code's native subagents; PaperGraph itself needs no model API key. Keep each task bounded
and dispatch independent work in parallel:

```text
author wave A   one Advocate per P-id + one Adversary
author wave B   one ClaimGrounder per claim_id
eval wave       one EvalAdvocate per K-id + one EvalAdversary + one ClaimAuditor
                + at least three blind Referees
```

The main Claude session is the Orchestrator. It is the only agent allowed to merge shared files.
Workers return structured findings or write only a pre-assigned disjoint path. Never allow two
agents to edit `paper.md`, `positions.md`, `claims.tsv`, `gate_report.md`, or the merged eval verdict
concurrently.

## Decision discipline

- Run both in-loop gates mechanically; do not replace their result with prose judgment.
- Treat both gates green as a candidate, not a release.
- Apply `eval/EVAL.md` fail-closed: no `SHIP` while D2, D3, D4b, or D5 is absent, even if the current
  harness exits successfully.
- Never use the author's position map as held-out ground truth.
- Never fabricate citations, quotes, numbers, or data provenance.
- Never weaken a gate or eval to clear an existing paper.

Read `DESIGN.md` for intent, `WORKFLOW.md` for execution, the two `gates/*.md` files for author-side
interfaces, and `eval/EVAL.md` plus `eval/protocol.md` for held-out evaluation.

Commit and push only when explicitly requested. If asked to push, use only
`github.com/VincentJiang06/PaperGraph` and branch before changing `main`.
