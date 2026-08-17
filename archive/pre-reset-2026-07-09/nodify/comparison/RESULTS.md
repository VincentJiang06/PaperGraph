# Three-mode ablation — does the logic tree actually help?

Same question ("AI agents 2020-2025 对就业的净效应?区分任务替代与岗位净增减"),
same model (Opus), same deliverable (~1500-word cited article), isolated runs.
The **only** variable is the framework:

- **raw** — no method, no tools (the long-markdown baseline)
- **skills** — a methodology-only skill (Nodify's *thinking discipline* — diverge-
  not-decompose, mandatory adversarial line, verbatim quotes, distill-then-discard —
  but NO tree, NO CLI)
- **tree** — full Nodify (nd CLI + skill)

This isolates two effects separately: raw→skills = the *discipline*; skills→tree =
the *machinery*.

## Blind judge panel (3 judges, mode-hidden, citations format-normalized, mean)

| dimension | raw | skills | tree |
|---|---|---|---|
| structure / logic | 4.00 | 5.00 | 5.00 |
| evidence quality | 3.67 | 4.00 | **5.00** |
| adversarial rigor | 3.00 | **5.00** | 4.67 |
| calibration | 4.00 | 5.00 | 5.00 |
| **overall** | **3.00** | **4.00** | **5.00** |

**Ranking: tree > skills > raw — unanimous across all 6 judge runs** (3 on a first
round + 3 on a re-run; see fairness note). Two honest nuances the panel surfaced:
1. **The discipline is the biggest single lever.** raw→skills is +1.0 overall,
   with adversarial rigor jumping 3.0→5.0. Much of the "quality" gain is *thinking
   method*, not tooling.
2. **The tree slightly trades adversarial systematicity** (4.67 vs skills' 5.0):
   the methodology's mandatory-adversarial section read as marginally more
   systematic. The tree's own `nd check` flagged this — 1 soft warning that one
   divergence layer lacked an adversarial direction. The framework *saw its own gap*.

## Mechanical metrics (objective)

| metric | raw | skills | tree |
|---|---|---|---|
| distinct sources cited | 8 | 9 | **18** |
| source text archived (durable, verbatim) | 11 KB (fragments) | 8 KB (fragments) | **66 KB (full, verified)** |
| verbatim quotes | ~12 | ~12 | **26** |
| quote fidelity | 92% (by diligence) | 92% (by diligence) | **100% (enforced by `nd check`)** |
| peak raw text in working context | **~18–22k tok** | ~4–5k tok | ~6–7k tok (1.5k verbatim) |
| citation provenance | 3 cites → secondary reproductions | primary | all primary, archived |

## Cold-resume probe (compaction immunity — the tree's headline claim)

Each mode's investigation was "interrupted"; a fresh agent had to recover it from
only what that mode persisted to disk.

| mode | recovery artifact | what a fresh agent recovered |
|---|---|---|
| raw | 11.7 KB unstructured source dumps, no conclusions | *"the analytical/synthesis state is genuinely unrecoverable — I recovered the source base but not the reasoning."* Had to re-derive from scratch. |
| skills | 4.3 KB research log | conclusions + figures recovered; **citations lost** (the log's citation section was an empty placeholder — a discipline slip) |
| tree | **2.9 KB structured `nd brief`** | full reasoning state: layers, leanings, specific figures, the adversarial line, **and the open coverage gap** — plus the exact next command. Missing detail was one `nd show` away, with *verified* quotes. |

## The honest answer

**Yes — the logic tree improves outcomes, but attribute the gains correctly:**

- The **thinking discipline** (available with or without the tree) is the largest
  lever for *article quality* and for keeping context lean. A disciplined agent with
  no tooling already beats raw by a full point and holds ~4× less raw text.
- The **tree** adds a further, real increment that is **not primarily about prose**:
  - **evidence depth** (2× the sources, judged 5.0 vs 4.0),
  - **enforced auditability** — 100% verbatim fidelity vs 92%, every claim traceable
    to a verified archive, no reliance on secondary reproductions,
  - **compaction immunity** — the *only* mode that preserved the reasoning state for
    recovery from a compact structured artifact,
  - **self-visible gaps** — `nd check` flagged its own missing-adversarial coverage.

The tree's value is **reliability, auditability, and recoverability**, which compound
where the discipline alone degrades: at scale, under interruption/compaction, with
weaker models, or when the output must be trusted and audited rather than just read.
On a single clean run by a strong model, raw still produced a serviceable article
(overall 3.0) — so the tree is not magic; it is a floor on rigor that does not depend
on the agent having a good day.

## Fairness note (instrument bug, disclosed)

The first blind-judge round used a blinding script that renumbered inline citations to
appearance-order but left reference numbers original — *introducing* a citation
misalignment, and only for raw/skills (the tree's references were bulletized). Judges
penalized it. Caught on review, the blinding was corrected to preserve each author's
own numbering (verified aligned for all three), and the panel was **re-run clean**.
The corrected round raised raw's evidence score (3→4) but did not change the ranking —
which is driven by evidence breadth, adversarial engagement, and source provenance,
none of which the bug touched. Both rounds ranked tree > skills > raw.

## Reproduce

`runs/{raw,skills,tree}/` — articles + sources + (tree) the nd session.
`python score.py .` — mechanical metrics. `python fidelity.py .` — quote fidelity.
`blinded/` — mode-hidden articles. `handoff/` — cold-resume artifacts.
`results.json` — aggregated scores.
