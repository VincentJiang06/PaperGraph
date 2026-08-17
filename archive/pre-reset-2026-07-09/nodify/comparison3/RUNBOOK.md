# comparison3 — aggressive-research eval RUNBOOK

Tests the one thing v1/v2 couldn't see: **does the logic tree let an aggressively-run
strong model (Opus) investigate better than the same aggressive method without a tree?**
Design + hypotheses: `../docs/10-aggressive-research.md`. **Nothing here has run yet.**

Arms (only variable = the tree; aggression + model held constant):
- **tree**  — aggressive skill + `nd` tree  (`skill/aggressive.md`, `PROMPT_tree.md`)
- **notree** — same aggressive method, markdown only (`PROMPT_notree.md`)

Judged artifact = the **investigation dossier** (uniform template), NOT an article.

## 0. Choose topics (launch-time decision)
Hard, open, multi-angle research questions that reward aggressive exploration. Put them
in `topics.md`. Recommend 3–5. (Econ questions from comparison2 work, or fresh open
ones — e.g. strategy/forecasting/root-cause questions with genuine competing hypotheses.)

Set the **budget dials** and **worker budget** (identical across arms) — e.g.
`--budget depth=4 width=8 open_claims=24`, ≤4 blitz-search workers per claim.

## 1. Author runs (Opus, 2 per topic)
For each topic T, create `runs/T/tree/` and `runs/T/notree/`, then dispatch two Opus
agents:
- tree:  follow `PROMPT_tree.md`; workspace `runs/T/tree`; question + budget in dispatch.
- notree: follow `PROMPT_notree.md`; workspace `runs/T/notree`; same question + budget.
Both may spawn blitz-search workers (same cap). Resume any that die (SendMessage).

## 2. Build dossiers
- tree arm:  `python3 dossier.py runs/T/tree`   → writes `runs/T/tree/dossier.md`
- notree arm: the author already wrote `runs/T/notree/dossier.md` (verify it exists +
  follows the template).

## 3. Mechanical metrics
`python3 tree_metrics.py . > results_mechanical.json`
`python3 fidelity.py runs/T/notree` (verbatim check on the skill-only arm; the tree arm
is verbatim-enforced by `nd check`). Descriptive; the judge is primary.

## 4. Blind + judge panel
`python3 blind.py .`                      → `blinded/<T>/dossier-A|B.md` + `KEY.json`
Audit leak-free (no `N-0`, `DOC-`, `nd`, `SYN-` in any blinded file).
Dispatch **3 Opus judges**, each follows `JUDGE_PROMPT.md`, scores every dossier, writes
`blinded/scores/judge-{1,2,3}.json`.
`python3 judge_aggregate.py . > results_judges.json`

## 5. Cold-resume probe (compaction under aggression — the headline test)
For each topic × arm, dispatch an Opus probe (`PROBE_PROMPT.md`): recover the reasoning
state from disk only — tree via `nd brief` (+ `nd show/tree/log`), notree via `log.md` —
**without reading `dossier.md`**. Score recoverability 0–5. This is where a big sprawling
run should separate the arms.

## 6. Aggregate + report
Combine into `results.json`; write `RESULTS.md` honestly (state which hypotheses in
docs/10 §5 held, which didn't — including H0/kill-criterion). Optional standalone HTML.

## Fairness notes to disclose in the writeup
- The notree author *writes* its dossier (could over-polish); the tree dossier is
  machine-generated from records. Mitigations: `fidelity.py` catches fabricated quotes;
  cold-resume uses the raw `log.md`, not the dossier; judges assess whether evidence is
  specific/verifiable.
- Keep worker budget + blitz-search permission identical across arms, or the comparison
  measures compute, not the tree.

## One-command dry-run (proves the scaffold, no author runs)
`python3 dossier.py ../comparison2/runs/T1/tree` renders a real tree into the template —
use it to sanity-check the pipeline before launch.
