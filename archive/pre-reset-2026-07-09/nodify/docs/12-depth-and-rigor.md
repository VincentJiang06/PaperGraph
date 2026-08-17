# 12 · Depth + rigor scaffold — the real target — ADOPTED (pre-build)

**Why (the whole arc, honestly):** v1–v3 showed the tree isn't a quality lever; v4
(comparison4) showed it's a memory/durability aid — *auxiliary*, not the point. User's
diagnosis (2026-07-09): **the thing worth building is a scaffold that makes the agent's
LOGICAL SEARCH deeper and more rigorous (深度 + 严密度). Memory was never the goal.**

**Identity constraint (user):** Nodify stays **a skill + a logic layer that HELPS an agent
do a task** — NOT a deep-research *pipeline* that reasons for the agent. We take
dzhng/deep-research and karpathy/autoresearch as **reference only**, not a lane-switch.

## The two mechanisms we borrow (as skill + logic, not a pipeline)

### A. Depth — findings-driven deepening (ref: dzhng/deep-research)
dzhng recurses: a level's *learnings + follow-up questions* become the next level's
queries; breadth halves, depth counts down. We port the *idea*, not the machinery:
- **Skill discipline:** when you *keep* a finding, immediately interrogate it — *"what
  deeper, consequential questions does this finding raise?"* — and pursue them. Keep
  going down until the deeper questions stop being both answerable AND
  judgment-changing (a real terminal, not satisficing / fatigue). Models stop early;
  the skill pushes past that.
- **Logic affordance:** `nd` tracks the depth reached per branch and surfaces **shallow
  concluded branches** (a claim concluded without ever spawning the deeper questions it
  raised) in `nd brief` / `nd check` — a visible nudge to go deeper, not a gate.

### B. Rigor — a keep-if-survives gate (ref: karpathy/autoresearch)
autoresearch hill-climbs against a hard metric: keep-if-better, revert-if-worse. Research
has no `val_bpb`, but the analog is an **adversarial evidence gate**:
- **Skill discipline:** a conclusion is *provisional* until you actively try to **refute
  it with evidence** — name what evidence would overturn it, go look for that, and **keep
  the conclusion only if it survives**. If it falls, revise or kill it. (Models are
  confirmation-biased about their own confident conclusions; the gate forces the
  disconfirmation attempt.)
- **Logic enforcement:** a new primitive **`nd challenge`** records a refutation attempt
  against a claim + its **outcome** (`survived` / `weakened` / `refuted`). A synthesis is
  **verified** only once it carries a resolved challenge; `nd check` flags
  **concluded-but-unchallenged** claims. This makes the rigor gate structural + auditable
  — the agent does the red-teaming, the logic proves it happened and what it found.

Together: **the tree stops being a place to record conclusions and becomes the thing that
pushes the search deeper (A) and won't let a conclusion count until it survived refutation
(B)** — while the agent, not the CLI, does the actual reasoning.

## The experiment (finally testing depth + rigor, in our lane)
- **Arms (both Opus, our lane):** *scaffold* = agent + depth/rigor skill + `nd`
  (challenge gate on) vs *plain* = agent + the plain aggressive skill (no depth-push, no
  challenge gate). Same model, same tools, same task. The only variable is the
  depth/rigor scaffold. (dzhng/autoresearch are reference, NOT a baseline arm — we are not
  racing their pipeline.)
- **Tasks: questions with CHECKABLE answers** — so rigor is scored against ground truth,
  not a judge. Two kinds:
  1. **Verifiable-fact investigations** — questions whose key sub-claims resolve to
     checkable facts (specific numbers, dated events, study results) where a plausible
     wrong answer is a known trap. Score: **correctness of the load-bearing claims**
     (did the challenge gate kill the plausible-but-false ones the plain arm kept?).
  2. **Depth probes** — questions that reward going N levels deep (a surface answer is
     wrong/incomplete; the right answer needs the deeper mechanism). Score: **depth
     reached** + whether the deep (correct) answer was found.
- **Metrics:**
  - **correctness / false-claim rate** — of the load-bearing conclusions, how many are
    actually true (checked against ground truth). *The headline for rigor.*
  - **depth reached** — max/median consequential follow-up depth per branch.
  - **challenge yield** — how many conclusions the gate revised/killed (and were those the
    wrong ones?).
  - (context/audit as before, secondary.)
- **Hypotheses:**
  - **H1 (rigor):** scaffold arm's false-claim rate < plain arm's — the challenge gate
    kills plausible-but-false conclusions the plain arm keeps.
  - **H2 (depth):** scaffold arm reaches deeper consequential follow-ups and finds
    deep-correct answers the plain arm misses by satisficing.
  - **H0 / kill-criterion:** if a strong model already deepens + self-refutes natively
    (scaffold ≈ plain on both correctness AND depth), the scaffold adds nothing and we
    say so — same honesty as every prior round. This is the real risk.

## Build order
1. This doc (done). 2. `nd challenge` primitive + `nd check` unverified-conclusion flag +
depth surfacing (logic). 3. The depth/rigor skill (discipline). 4. The checkable-answer
task set + eval harness (correctness-scored). 5. Run scaffold vs plain, report honestly.
