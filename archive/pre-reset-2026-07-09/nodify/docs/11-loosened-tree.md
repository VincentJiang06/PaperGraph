# 11 · Loosened tree (v0.2) + the compaction-scale test — ADOPTED

**Why (from the evidence):** v1→v2→v3 established that the tree is not a quality lever;
in v3 (aggressive Opus) the *rigid* structure actively hurt — it was systematic but
missed the reframes the free arm found. User decision (2026-07-09): **keep the tree
method, but loosen it so reframes are cheap and budgets don't coerce, and test it only
where durability actually matters — investigations that must compact-and-reload.** This
doc is the source of truth for that change.

## What loosened (code: `tree.py`, `checks.py`, `cli.py`)
1. **Cheap reframe — `nd reframe N --statement … [--note]`.** Rewrites a node's statement
   **in place** (same `node_id`), so children + doc bindings are untouched. Works on the
   **root** (the framing question is no longer fixed at init). Distinct from `revise`
   (which mints-new + retires, for claim narrowing with a lineage — still refuses the
   root and now points here).
2. **Cheap restructure — `nd reparent N --to M [--note]`.** Moves a node and its whole
   subtree under a new parent; children + bindings follow automatically (nothing
   references `parent_id`). Guards only against cycles and reparenting the root.
3. **Free kind.** Dropped "children of a viewpoint must be viewpoints / of a claim must
   be claims." A claim may be added straight under a viewpoint (`add --kind claim`) — no
   forced promote ceremony. `promote` still exists (re-kind in place) but is optional.
   Root must still be a viewpoint.
4. **Budgets are soft guardrails, not gates.** `max_depth / max_children /
   max_open_claims` no longer BLOCK any write (removed from `add`, `promote`, `revise`).
   `nd check` surfaces over-guardrail sprawl as **soft warnings** so the model can *see*
   it going wide/deep — but **convergence is the model's judgment, not the CLI's.**
   Budget-as-epistemology is gone.

**No schema change (P5 respected):** reparent/reframe append `node.v1` records with a
changed `parent_id`/`statement` under the same `node_id` — exactly how `set-status`
already versions a node (append-only, latest-per-id wins). CLI surface: +2 commands
(`reparent`, `reframe`) → closed list mirrored in `test_cli`. Tests updated to the new
spec (never weakened): the old budget-gate / kind-rigidity assertions became
soft-guardrail / free-kind / reparent / reframe assertions. 60 tests green.

## The test that fits the tool: compaction-scale (comparison4/)
The tree's value proposition is **durability under compaction** — it only pays off when
the investigation **exceeds what one context can hold**. Every prior eval used
context-fitting tasks, so the tree could not win. The new protocol forces the regime:

- **One big investigation, run in PHASES under forced compaction.** Each phase is a
  **fresh agent** that inherits **only what is on disk** — the tree + `nd brief` (tree
  arm) or the markdown `log.md` (notree arm) — never the previous agent's context. It
  reads the persisted state, does more investigation, checkpoints, and hands off. Repeat
  for N phases (≥4–6 compaction cycles).
- **Arms:** skill+tree (loosened) vs skill-only markdown, both Opus, both aggressive/free.
- **Metrics:**
  - **can-complete / continuity** — did each fresh agent *continue* (extend the same
    investigation coherently) or *restart / drift / duplicate*?
  - **final investigation quality** — blind judge on the uniform dossier (the 6 dims).
  - **grounding/auditability** — enforced (tree) vs self-managed (notree).
  - **memory growth** — does the notree `log.md` **balloon** across phases (must re-read
    an ever-larger blob) while the tree `brief` stays **bounded**? This is the crux: the
    tree wins iff, as the investigation grows past context size, the notree memory either
    blows up or degrades while the tree's frontier-only brief stays cheap + complete.
- **Hypotheses (pre-registered):**
  - **H1:** over ≥4 compaction cycles the notree log's size grows ~linearly and
    eventually its re-read cost / fidelity degrades; the tree brief stays bounded.
  - **H2:** tree-arm continuity ≥ notree-arm continuity (fewer restarts/dupes) as cycles
    accumulate.
  - **H3:** final grounding/auditability: tree > notree (enforced).
  - **H0 / kill-criterion:** if, even under many forced compactions on an oversized task,
    the notree arm keeps up on continuity AND its memory stays manageable, the tree's
    durability value is not demonstrated — and we say so.
- **Fairness:** identical phases, identical compaction points, identical task; the only
  variable is tree vs markdown. Disclose that the notree author *hand-writes* its brief/
  log each phase (its best case) while the tree brief is machine-generated.

Runbook + scripts: `comparison4/`. Nothing about this doc's claims is proven until that
runs; H0 is a real possible outcome.
