# Aggressive research — WITH the logic tree (skill+tree arm)

You are running an **aggressive/wild deep-research investigation** on a hard, open
question, using the **nodify** framework as your governor. Read and follow this skill
in full — it is your operating logic:
/Users/vince/playground/Paper Graph/nodify/skill/aggressive.md

Be genuinely aggressive: fan out MANY distinct lines fast (including contrarian ones),
open dedicated red-team branches against your leading hypotheses, dispatch parallel
search workers, kill thin branches fast, then converge hard. The tree keeps it grounded,
adversarial, auditable, and convergent — lean on it.

## nd invocation
- Binary: `/Users/vince/playground/Paper Graph/.venv/bin/nd`
- `cd` into your assigned workspace, then init with the budget from your dispatch —
  **one `--budget` flag per key**, keys are `max_depth/max_children/max_open_claims`:
  `nd init cmp --question "<the question>" --boundary "<scope>"
   --budget max_depth=<k> --budget max_children=<k> --budget max_open_claims=<k>`.
- Root is fixed at init; the **first `nd add` builds the root viewpoint**, then
  `nd add --parent N` for facets. Claims aren't added directly under a viewpoint —
  `nd add` a viewpoint then `nd promote N` to re-kind it to a claim.
- Run all later `nd` commands from the workspace. `--file` shapes: `nd schema …`.

## The deliverable is the TREE, not prose
- Build a wide, deep, fully-grounded tree; converge to a **root synthesis** with
  calibration + explicit `open_questions`. **Do NOT write an article.**
- Every conclusion grounded (evidence → archived doc_id, quotes verbatim); every
  viewpoint has ≥1 adversarial line; run `nd check` often and keep it clean.
- When done: `nd check` (report result), leave `sessions/cmp/` intact. **Do not** write
  a dossier yourself — it is generated from your tree by the harness.
- Your final message = one line: # viewpoints / # claims / # DOC archived / nd check result.

## Fairness (identical across both arms)
- Blitz-search subagents are ALLOWED (aggression is the point) — but keep to the same
  budget of workers stated in your dispatch. Workers save cited page text to `notes/`;
  you distill and discard raw text. Do not read or write anything outside the workspace.
