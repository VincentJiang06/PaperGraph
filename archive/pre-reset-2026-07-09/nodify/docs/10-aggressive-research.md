# 10 · Aggressive research mode + its eval — ADOPTED, pre-launch

**Status:** design frozen; scaffolding built under `comparison3/`; **not yet run**.
This doc is the source of truth for the "aggressive research" (激进科研) direction and
the experiment that will validate it.

## 1. Why this, and why now

The v1 and v2 ablations (`comparison/`, `comparison2/`) established one thing firmly:
**the thinking discipline is the biggest quality lever, and it does not need the tree.**
On careful single-pass runs the tree ≈ discipline on judged quality (v2 spread 0.20).
So the tree must earn its keep in a regime the careful ablations could not see.

**The thesis.** A strong model (Opus-class) has reasoning horsepower that a cautious
protocol under-uses. If you deliberately **unleash** it — wide, fast, bold, high-
divergence exploration with heavy parallel search — a *bare* run sprawls: it loses the
thread, drops grounding, can't converge, and blows its context. The **logic tree is the
governor** that lets you run aggressively *without* losing rigor: every claim stays
grounded + verbatim-audited, every viewpoint keeps an adversarial line, everything lands
(auditable), context stays lean under a firehose (distill-then-discard), and the budget
forces convergence. **Engine + chassis.** The tree's value shows up precisely under
aggression — which is where it should have mattered all along.

## 2. What the deliverable is (and is NOT)

**The judged artifact is the node/tree — the *investigation* — not an article.** Prose is
generated downstream by the compiler skill (PaperGraph), which is out of scope for
evaluating Nodify. We evaluate the tree the aggressive process builds: its coverage,
depth, adversarial completeness, grounding/auditability, and convergence. The
aggressive skill (`skill/aggressive.md`) explicitly ends at the **root synthesis + the
`nd export` dossier**, and forbids essay-writing.

## 3. The aggressive logic (summary; full text in `skill/aggressive.md`)

Six principles, each a "be wild" paired with a "tree makes it non-negotiable":
1. **Blitz divergence** — fan out many distinct angles at once (incl. contrarian), land all immediately. *Tree: everything is on the tree or it doesn't exist.*
2. **Hypothesis-first, disconfirm-hard** — bold conjectures early, then a dedicated red-team branch to kill the leading one. *Tree: ≥1 adversarial line per viewpoint, enforced by `nd check`.*
3. **Blitz-search** — many parallel search subagents per claim; distill reports, discard raw text. *Tree: distill-then-discard keeps context lean under the firehose.*
4. **Kill fast, log why** — retire thin branches quickly. *Tree: auditable graveyard; every retire/stuck carries a `--note`.*
5. **The tree is the only brake** — wild in *what/how-fast*; the tree makes grounding, verbatim quotes, adversarial coverage, landing, and forced convergence non-negotiable.
6. **Escalate then converge** — spend budget expanding, then ruthlessly roll up to a calibrated root synthesis with explicit open gaps.

## 4. The experiment — isolate the tree, hold aggression constant

Both arms use **the same aggressive skill** and **the same strong model (Opus)**. The
**only variable is the tree.**

| arm | thinking | persistence | output |
|---|---|---|---|
| **skill+tree** | aggressive skill | `nd` durable tree (grounding/adversarial/verbatim/convergence enforced) | `nd export` dossier |
| **skill-only** | aggressive skill | a single markdown research log (author-managed, nothing enforced) | a dossier the author writes in the same template |

No "raw" arm — discipline is a settled baseline; the question is strictly *what the tree
adds on top of an already-aggressive, already-disciplined strong model.*

### 4.1 The judged artifact: a uniform Investigation Dossier
To blind-judge tree vs no-tree without format leakage, **both** arms are rendered into
one identical template (`dossier.py` builds it deterministically for the tree arm from
`nodes.jsonl`/`syntheses.jsonl`/`docs`; the skill-only author writes theirs to the same
template). Template:

```
# Investigation: <question>
## Lines of inquiry
### L<k>: <viewpoint statement>   [orientation: neutral|adversarial]
  - claim(s): <the minimal investigable question(s)>
  - conclusion: <lean> — <one-line summary>
  - evidence: [ <source title> — <url> — "<verbatim quote>" ] × n
  - adversarial line: <what was tried to refute it, and what that found>
## Dead ends / retired
  - <branch> — <why killed>
## Root conclusion
  <calibrated synthesis> (confidence: …)
## Open gaps
  - <what remains unresolved / unverified>
```
Content differences (an ungrounded claim, a missing adversarial line, an unconverged
sprawl) show up as **gaps in the dossier** — legitimate quality signal, not format leak.
The blinder normalizes headers/citation tokens exactly as in `comparison2/blind.py`.

### 4.2 Blind judge panel (investigation quality, NOT prose)
3 Opus judges, mode hidden, per topic, integer 1–5 on:
- **coverage / breadth** — # of genuinely distinct, relevant lines (incl. contrarian) actually pursued.
- **depth** — how far each line was pushed (mechanism/quant, not surface).
- **adversarial completeness** — were leading hypotheses genuinely red-teamed; disconfirming evidence sought *and integrated*.
- **grounding / auditability** — is every load-bearing claim tied to a specific verifiable source + verbatim quote; trustworthy without re-checking.
- **coherence / convergence** — do the many lines integrate into a calibrated conclusion, or is it a disconnected sprawl.
- **calibration & honesty** — open gaps named, uncertainty stated, dead ends recorded.

### 4.3 Mechanical metrics (descriptive; asymmetric by nature)
On the working artifacts, uniform where possible:
- coverage: # lines of inquiry, # claims, tree depth/width, # adversarial branches.
- **grounding rate**: fraction of conclusions carrying ≥1 evidence pointer.
- **verbatim fidelity**: quotes that actually appear in saved sources (tree = enforced by `nd check`; skill-only = checked post-hoc with `fidelity.py`).
- **sprawl / context load**: raw-text volume the arm accumulated (log size / notes bytes) — proxy for "did ungoverned aggression blow context."
- `nd check` clean (tree arm only).

### 4.4 Cold-resume probe (compaction under aggression)
The headline stress test. An aggressive run produces a *big, sprawling* investigation;
interrupt it and recover from disk only — tree via `nd brief`, skill-only via its log
(NOT the dossier). Score reasoning-state recoverability 0–5 (as in comparison2). The
tree should separate here: `nd brief` stays bounded and complete; a large markdown log
is where recovery degrades.

## 5. Hypotheses (pre-registered — state them before the run)
- **H1 (grounding/audit):** skill+tree ≫ skill-only on grounding/auditability and verbatim fidelity — the tree enforces it, ungoverned aggression skips it.
- **H2 (convergence):** skill+tree > skill-only on coherence/convergence — the budget + roll-up force a calibrated conclusion; ungoverned aggression sprawls.
- **H3 (coverage):** skill+tree ≥ skill-only on coverage — the tree lets you hold more live lines without losing them; possibly a *wash* if Opus can juggle a lot in-context.
- **H4 (compaction):** skill+tree ≫ skill-only on cold-resume under a large investigation.
- **H0 / kill-criterion:** if skill+tree shows **no** advantage on grounding, convergence, OR compaction even under aggression, the tree's value proposition is not supported and we say so (as we did in v2).

## 6. Run shape (default: I orchestrate via subagents; portable to your pipeline)
Topics: N hard, open, multi-angle research questions (rich enough to reward aggression).
Per topic: 2 author runs (skill+tree, skill-only), Opus, single-context research
allowed (blitz-search subagents permitted for BOTH arms — aggression is the point — but
kept symmetric). Then: `dossier.py` → `blind.py` → 3 Opus judges → `judge_aggregate.py`;
`tree_metrics.py` + `fidelity.py` mechanical; cold-resume probes. Full steps in
`comparison3/RUNBOOK.md`. Nothing runs until the launch go-ahead.

## 7. Open design decisions to confirm at launch
- **Topic set + N** (how many, which questions). Aggression rewards open/contested questions.
- **Blitz-search symmetry**: allow both arms to spawn search workers (recommended — tests the *governor*, not compute), or forbid for both (tests pure in-context aggression). Must be identical across arms.
- **Budget dials** for the tree arm (depth/width/open_claims) — how wild.
