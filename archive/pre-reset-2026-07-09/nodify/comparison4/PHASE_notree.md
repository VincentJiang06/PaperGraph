# Compaction-scale investigation — NOTREE arm, one phase

You are **one phase** of a long investigation being run under **forced compaction**. You
have **NO memory** of any previous phase — everything you know must come from **disk**.
Your dispatch says which phase number you are and whether it's the final one. You have
**no `nd` tool**: your entire persisted memory is a markdown log you manage yourself.

## Method + rule
- Method: same aggressive/free research method (wide, hypothesis-first, red-team, ground
  every claim in a **verbatim** quote, restructure your notes when a better framing
  appears, converge at the end).
- **WORKER BUDGET = 0**: research yourself in this one context (symmetric). No subagents.

## First action (ALWAYS)
`cd` into your workspace, then:
- **If phase 1**: create `log.md` — a structured research log (the big question, your
  planned lines of inquiry, a Findings section, a Graveyard for killed lines) — and start
  cataloguing studies.
- **If phase > 1**: **read `log.md` FIRST — it is your ONLY memory.** Do not assume any
  context beyond it. Continue the *same* investigation; do not restart or duplicate.

## What to do this phase (bounded — you will NOT finish)
Advance the evidence map by a **bounded** amount (~**6–10 new studies/claims** this
phase), then stop and hand off:
- For each study: design, sample, effect size + direction, key limits — with a **verbatim
  quote** from the source, and **save the source's fetched text** to `sources/S<n>.txt`.
- Keep ≥1 adversarial line per facet; log killed lines in the Graveyard.
- **Append your progress to `log.md`** (and reorganize it if a better structure appears —
  it must stay a faithful, usable memory for the next phase).
- Keep `log.md` a working memory, not a transcript — but it must be complete enough that a
  fresh agent with only this file could continue.

## If your dispatch says FINAL phase
Do a last advance, then **converge**: write the calibrated synthesis, and produce
`dossier.md` in the standard template (the harness will judge it):
```
# Investigation: <question>
## Lines of inquiry
### L1 [orientation: neutral|adversarial]
  - statement: …
  - conclusion: [<lean>/<confidence>] …
  - evidence:
      - <title> — <url> — "<verbatim quote>"
## Dead ends / retired
## Root conclusion
[<lean>/<confidence>] …
## Open gaps
```

## Deliverable
Keep `log.md` + `sources/` (and on the final phase, `dossier.md`). Your final message =
one line: phase #, # new studies this phase, current `log.md` size, whether you
restructured the log.
