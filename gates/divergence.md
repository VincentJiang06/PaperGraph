# Gate 1 — DIVERGENCE (objectively measured)

**Claim of the gate:** the paper engages the *field's real space of positions* — not a
strawman set — plus the single strongest objection to its thesis. Divergence is **produced**
by fan-out and **enforced** by a coverage count. This is the humanities-side `val_bpb`.

## What "divergent enough" means (the ground truth: `positions.md`)
An independent **cartographer** subagent maps the *field's* position-space for the thesis —
what a well-read opponent would insist belongs in the debate — and writes `positions.md`.
The paper does not get to define its own opponents; the map does.

## The map — `runs/<slug>/positions.md`
One block per position. The gate parses these fields, so keep the exact headers:
```
## P1: <short position name>
holder: <who actually holds it — school/author/camp>
claim: <the position's core claim, one sentence, its strongest form>
rests_on: <the evidence or value it stands on>

## P2: ...

## STRONGEST-OBJECTION
claim: <the single strongest objection to THIS paper's thesis>
rests_on: <what would have to be true for the thesis to be wrong>
```
Rules: ≥ 3 real positions that genuinely disagree (not three flavors of one view). Exactly
one `STRONGEST-OBJECTION` block. Cartographer maps the field, never the paper.

## How the paper signals engagement
In `paper.md`, engaging a position means making a **real argument about it** — steelman then
answer, concede, or refute with reason — and tagging that passage with the id:
- `[P1]` … `[Pn]` inline where the paper genuinely engages that position.
- `[OBJ]` where the paper answers the strongest objection.
- An `## Excluded` section may list positions deliberately out of scope, one line of reason
  each: `- [P4] out of scope because …`. Excluded-with-reason counts as *handled* (engaged
  or excluded), but **not** as *engaged*. A bare tag does not count: the gate measures the
  whole **paragraph** (blank-line block) around each tag and requires real argument prose
  (≥ 200 non-tag chars), so a namedrop on a wrapped line is rejected.

> **What the gate does and doesn't prove.** It enforces *structural coverage* — that every
> field position is addressed in a substantial paragraph (or consciously excluded) and the
> strongest objection is answered. It cannot judge whether that paragraph is a *good* steelman;
> argument quality is the orchestrator's and subagents' job, not the gate's. The gate is the
> necessary floor, not the sufficient condition.

## The gate (`python3 gates/divergence_gate.py runs/<slug>`)
Computes, from `positions.md` ↔ `paper.md`:
- **coverage = handled / total positions**, where handled = engaged (`[Pi]` with real
  argument) **or** explicitly excluded with a reason.
- **engagement = engaged / total positions** (excluded does not count here).
- **objection-engaged =** is `[OBJ]` present with a real argument (yes/no).
Writes both rates into `gate_report.md`. **PASS** iff `coverage == 1.0` (every position is
either engaged or consciously excluded), `engagement ≥ K`, **and** objection-engaged = yes.
`K` = the field-weight threshold: humanities-heavy `0.8`, mixed `0.6`, science-heavy `0.5`
(a science paper still owes the strongest objection + conscious exclusion of the rest).

## Revise on failure
Uncovered position → engage it (steelman + answer) or move it to `## Excluded` with an honest
reason. Objection unaddressed → answer it or concede scope. Never delete a position from
`positions.md` to raise the score — the map is the field's, not the paper's.
