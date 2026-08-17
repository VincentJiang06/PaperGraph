# Task: deep-research academic article (research methodology — discipline only)

You are doing a deep research investigation and writing a short academic article.
Follow the methodology below. Keep your working state in a **single markdown
research log** (`<workspace>/log.md`); there is no special tooling — you manage it
yourself.

## Structure your thinking as claims, not prose
- Break the question into **viewpoints** (abstract positions/sub-questions) and
  **claims** (minimal, directly-investigable questions).
- **Diverge, don't decompose**: a good sub-question can be answered *without
  assuming the parent is true* (independence test).
  ✅ "AI导致就业下降" → "AI 擅长/不擅长哪类任务?"(独立可答)
  ❌ "AI导致就业下降" → "下降了多少?"(预设了下降)
- For every position you explore, **deliberately open at least one adversarial
  line** — a sub-question whose answer, if yes, would *refute* your leaning.

## Evidence discipline
- When you cite a source, use a **verbatim quote** copied exactly from the page
  (never paraphrase-as-quote, never stitch fragments). Save the source text so a
  reader could verify it.
- Every conclusion must name the evidence it rests on. Distinguish what the
  evidence **supports** vs **refutes** vs is merely **context**.
- If the evidence is insufficient, say so explicitly rather than overclaiming.

## Work loop
1. In `log.md`, list the viewpoints and the claims each spawns.
2. Investigate each claim (real web search, **yourself in this one context — do
   not spawn subagents**); record findings with source title + URL + the verbatim
   key line.
3. Conclude each claim: a one-line lean (supports/refutes/mixed) + summary +
   the evidence it rests on + open questions.
4. Roll conclusions upward: each viewpoint's conclusion cites its sub-claims.
   The root conclusion is your thesis.
5. Keep the log lean — record the *logic and evidence*, discard raw page text
   once distilled. Don't let the log balloon into a transcript.

## Citations (required, uniform format)
- Cite inline as `(S1)`, `(S2)`, … in the article body.
- For **every source you actually cite**, save the fetched page text to
  `<workspace>/sources/S<n>.txt`. One file per distinct source, matching the
  inline number.
- End the article with a `## 参考文献` list mapping S1, S2, … to title + URL.

## Article
- Write a Chinese (中文) academic article grounded in your conclusions. **HARD
  LENGTH CONSTRAINT: the body MUST be 1500–1800 中文字** (excluding the References
  section) — fixed for cross-arm comparability. This is a hard, contested question —
  engage competing explanations, reason through mechanisms, reach a calibrated view.
  Include a counterpoints/discussion section that honestly engages the adversarial
  lines. Depth of reasoning, not length.
- Output: `<workspace>/article.md` (keep `log.md` alongside it). Then stop.
- Your final message = a one-line note of how many sources you cited.
