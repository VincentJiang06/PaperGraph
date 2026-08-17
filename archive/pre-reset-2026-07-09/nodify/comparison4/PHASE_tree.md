# Compaction-scale investigation — TREE arm, one phase

You are **one phase** of a long investigation that is being run under **forced
compaction**. You have **NO memory** of any previous phase — everything you know must
come from **disk**. Your dispatch says which phase number you are and whether it's the
final one.

## The tool + the rule
- nd binary: `~/playground/Paper Graph/.venv/bin/nd`
- Method skill (read it): `~/playground/Paper Graph/nodify/skill/aggressive.md`
  (loosened v0.2: budgets are soft; **reframe/reparent are cheap** — restructure freely).
- **WORKER BUDGET = 0**: do the research yourself in this one context (symmetric with the
  notree arm). No subagents.

## First action (ALWAYS)
`cd` into your workspace, then:
- **If phase 1** (no session yet): `nd init cmp --question "<the big question, given in
  dispatch>"` then build the root viewpoint + an initial fan-out of facets, and start
  cataloguing studies.
- **If phase > 1**: run `~/playground/Paper Graph/.venv/bin/nd brief` FIRST and
  work only from what it shows (drill with `nd tree` / `nd show` / `nd docs for-node` /
  `nd recall`). **Do NOT try to recall context you don't have — the tree is your memory.**
  Continue the *same* investigation; do not restart it or duplicate existing nodes.

## What to do this phase (bounded — you will NOT finish)
Advance the evidence map by a **bounded** amount (roughly **6–10 new studies/claims**
grounded this phase), then stop and hand off:
- Add nodes for new studies/facets (`nd add`; kind is free — attach claims directly).
- Investigate (real web search, yourself), **ingest each cited source** (`nd docs ingest`,
  verbatim quote), and **conclude** each claim (`nd conclude`, evidence → doc_id, quote
  verbatim). Ground everything.
- Keep ≥1 adversarial line per facet.
- **If the accumulating map suggests a better structure, restructure cheaply** —
  `nd reframe` (rewrite a node's framing in place, incl root) / `nd reparent` (move a
  subtree). This is encouraged; don't stay stuck in an early decomposition.
- Write partial viewpoint-level syntheses as facets fill in.
- Run `nd check`; keep it clean (soft warnings OK).

## If your dispatch says FINAL phase
Do a last advance, then **converge**: write viewpoint-level syntheses and the **root
synthesis** (calibrated conclusion + confidence + explicit open_questions). Then run
`nd check`.

## Deliverable
Leave `sessions/cmp/` intact (the harness generates the dossier). Do NOT write an article
or dossier. Your final message = one line: phase #, # new nodes this phase, total docs,
whether you reframed/reparented, `nd check` result.
