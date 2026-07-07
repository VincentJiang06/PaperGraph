# PaperGraph

PaperGraph is a research framework that runs under Claude Code. It treats linear "write the paper top to bottom" workflows as harmful to argument quality, and instead:

1. Builds the paper's ideas as a **Logic Graph** (claims = nodes, argumentative moves = directed, strength-classed edges), expanded layer by layer.
2. Proves every node and edge atomically with a **Proof Machine** — bounded, parallel Claude workers fill fixed check forms ("in scope? evidence sufficient? inference holds?"); code computes the verdict from each form via a published decision table.
3. Archives all literature in a **Docs Database** with memoized search, so evidence is found once, reused forever, and citations cannot be hallucinated.
4. Produces prose exactly once, at the final **Compiler** step, from a frozen, evidence-bound argument — then audits it.

It is not an autonomous paper writer and not a RAG chatbot. It makes arguments verifiable before prose exists.

## Repository State

Spec-only. `docs/` is the complete, current specification; implementation starts from `docs/10-v1-design.md` milestone M0.

```text
docs/        the specification (read 00 → 12 in order)
examples/    topic-input-p4.md — the test topic used by milestone acceptance
product/     product form, usage patterns, go-to-market planning (not build spec)
archive/     legacy documentation, superseded, do not use
```

## The Documents

Four layers: **modules** (01–07), **binding contracts** (08–09), **the concrete first version** (10), **the executable test plan** (11).

```text
docs/00-overview.md             what PaperGraph is; component map; non-negotiables; r2 changelog
docs/01-topic-and-scoping.md    topic input file, parsing rules, PaperSpec, ProjectContract
docs/02-logic-graph.md          nodes, edges, lifecycle, BFS expansion, spine, MSA checklist
docs/03-proof-machine.md        proof tasks, evaluation ladder, decision table, worker protocol
docs/04-docs-database.md        documents, EvidenceUnits, matcher algorithm, memoized search
docs/05-workflow-and-queue.md   pipeline, queue state machine, gates, parallelism rules
docs/06-compiler-and-audit.md   freeze, dry run, section plan, draft map, prose, audit
docs/07-runtime-and-tooling.md  storage layout, ids, snapshots, CLI, worker dispatch, WebUI
docs/08-module-contracts.md     AUTHORITATIVE boundary contracts: artifact ownership,
                                pre/postconditions, verdict→action map, failure policy
docs/09-verification.md         shared text algorithms, V-* validation rule registry,
                                integration scenarios, invariant sweep, trace chain
docs/10-v1-design.md            v1 scope and stack, per-command CLI contracts,
                                worker prompts, milestones M0–M4, definition-of-done demo
docs/11-test-suite.md           AUTHORITATIVE test plan: fixtures, FakeWorkers, golden
                                decision rows, hostile catalog, meta-tests, milestone gates
docs/12-webui-spec.md           AUTHORITATIVE WebUI design: shell, tokens, views,
                                components, accessibility, test hooks
docs/13..18                     the SEARCH PROGRAM (S1-S5): design-frozen, staged
                                specs for thorough evidence search — planning,
                                waves+critic, source tiers, saturation, semantic
                                retrieval; binding only on adoption (docs/13)
```

## Core Loop (first thing to build)

```text
seed edge A -> B
  -> ProofTask (+ ContextPack + DocsPack)
  -> parallel Claude ProofWorkers write check-form files
  -> Validator checks the form and COMPUTES the verdict (decision table)
  -> Committer (only graph mutator): edge -> needs_repair(bridge), bridge nodes C/D enqueued
  -> loop until Minimal Sufficient Argument
  -> Freeze -> Compiler dry run -> prose -> Audit
```

## Non-Negotiables

```text
JSON/JSONL is canonical state; DB/cache is derived and rebuildable.
Committer is the only Logic Graph mutator.
Workers fill closed-enum check forms along the evaluation ladder; code computes
  verdicts — no AI numeric scoring of academic judgment.
Inference gaps get at most 2 bridge proposals; no recursive expansion inside proof tasks.
Docs never sets verdicts; Proof never searches; Compiler never adds claims; Audit never rewrites.
No prose before the Compiler stage.
Every citation resolves to an archived Document.
Parallel workers have disjoint output files; shared state passes through gates.
```

## Naming

```text
Product:      PaperGraph
Package/CLI:  paperproof
Source root:  src/paperproof/
Data root:    data/projects/<project_id>/
```
