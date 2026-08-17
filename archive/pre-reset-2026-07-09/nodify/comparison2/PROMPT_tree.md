# Task: deep-research academic article (full nodify — durable logic tree + nd CLI)

You are doing a deep investigation and writing a short academic article, using the
**nodify** framework. Do not pile state in your context: **context holds only the
frontier; the truth lives on the tree.** The tool is `nd` (each command prints one
JSON envelope; every persisted record is schema-validated).

## nd invocation (IMPORTANT)
- Binary: `/Users/vince/playground/Paper Graph/.venv/bin/nd`
- **First**, `cd` into your assigned workspace (given in your dispatch message),
  then `nd init cmp --question "<the assigned question>" --boundary "<scope>"`.
  This creates `./sessions/cmp/`. Run all later `nd` commands from the workspace.
- `--file` command shapes are printed by `nd schema conclude|ingest|outline|expand`
  — don't guess JSON; read the schema + example. The session/notes dirs are in the
  init/brief envelope (`session_dir` / `notes_dir`); the scratch area is
  `<session_dir>/notes/`.

## Core loop (the nodify method)
1. **Diverge (viewpoint layer)**: `nd add --parent N --statement "…" --why "…"
   [--orientation adversarial]`. Diverge ≠ decompose — a legal sub-direction can be
   answered *without presupposing the parent is true*. **Every divergence opens at
   least one `adversarial` direction** (a line that would refute the parent). Land
   each viewpoint on the tree immediately; don't batch — context is disposable, the
   tree is not.
2. **Promote (viewpoint → claim)**: when a viewpoint yields no new
   judgment-changing direction, `nd promote N --note "directions tried / why
   exhausted / expected evidence shape"`. A claim is a **minimal, directly
   investigable** question.
3. **Investigate (evidence layer)**: `nd recall --node N --query "…"` first (skip
   only if the index is obviously empty). Then `nd set-status N investigating` and
   **do the web research yourself, in this one context** (WebSearch + WebFetch).
   > FAIRNESS CONSTRAINT: do **not** spawn subagents for this task — the baseline
   > arms research in a single context, so you must too, to keep total compute
   > comparable. The tree (not sub-workers) is where you keep durable state: land
   > distilled logic + archived evidence as you go, and discard raw page text from
   > your context once distilled. You are the tree owner: gather, judge sufficiency,
   > distill — don't let raw text pile up in context.
4. **Distill (archive before you discard)**: process each worker report immediately,
   discard the raw text. Archive the sources a conclusion actually rests on:
   `nd docs ingest --file entry.json` ({kind,title,url?,text_file,summary≤500,
   bindings:[{node_id,relation}]}) — same text auto-dedups. Reuse an archived entry
   for another node with `nd docs bind DOC-xxxx --node N --relation R`. Then conclude:
   `nd conclude --file syn.json` — evidence entries point at archived docs by
   **doc_id**; quotes must be **verbatim** (non-verbatim is auto-degraded + warned;
   paraphrase rather than fabricate). Insufficient evidence → refine ≤2 rounds, else
   `nd set-status N stuck --note "what's missing" --reason evidence`.
5. **Converge (roll up)**: when a viewpoint's children answer it, write a
   viewpoint-level synthesis (`based_on.children`). The root synthesis is the final
   answer.
6. **Write (article layer)**: after the tree converges —
   `nd article outline --file ol.json` ({title, thesis, grounded_in:[SYN…],
   sections:[{section_id S-01, title, role, node_ids, intent}], excluded:[{node_id,
   reason}]}): the thesis must be grounded in existing syntheses; **excluded
   branches need a reason**.
   > HARD LENGTH CONSTRAINT (for cross-arm comparability): the assembled article
   > body MUST be **1500–1800 中文字 total** (excluding the References section).
   > Use **at most 4 sections** of ~400 字 each so the total lands in range — this
   > OVERRIDES the default per-section length. Depth of reasoning, not length.
   Draft each section (in body text, cite as
   `(cite: DOC-xxxx)` — only archived entries; **no self-authored section titles** —
   assemble adds them), register with
   `nd article section --id S-01 --file draft.md` (dangling cites are hard-rejected),
   then `nd article assemble` → writes `final.md` (References auto-generated).

## Discipline (`nd check` watches)
- Run `nd check` often; fix hard errors immediately; soft warnings (no adversarial,
  ungrounded conclusion, unpointered evidence, unreasoned retire) are your laziness
  list — keep it short.
- Status changes always carry `--note`. Budget (depth/width/open-claims) is the leash
  on greedy divergence.

## The question is HARD and contested — reason deeply
This is a hard economic-analysis question with competing explanations. Use the tree
to diverge into genuinely independent lines (including adversarial ones), investigate
each with evidence, and converge to a calibrated thesis. Depth of reasoning matters
more than length.

## Output (REQUIRED for scoring)
- After `nd article assemble`, **copy the assembled article to `<workspace>/article.md`**
  (`cp sessions/cmp/article/final.md article.md`, or write it there).
- Leave the `sessions/cmp/` session intact (tree, docs store, synthesis).
- Run a final `nd check` and make sure it is clean (or only expected soft warnings).
- Your final message = one line: how many DOC entries archived + `nd check` result.
