# Task: deep-research academic article (baseline — no method, no tools)

You are writing a short academic article based on real web research. Work however
you naturally would. There is no prescribed method and no special tooling.

## Deliverable (write to the workspace path given in your dispatch message)
- A Chinese (中文) academic article answering the assigned question with depth and
  rigor. **HARD LENGTH CONSTRAINT: the body MUST be 1500–1800 中文字** (excluding
  the References section) — this is fixed for cross-arm comparability. This is a
  hard, contested question — engage the competing explanations, reason through
  mechanisms, and reach a calibrated view. Depth of reasoning, not length.
- Do **genuine web research** (WebSearch + WebFetch) **yourself, in this one
  context** — do not spawn subagents.
  Aim for solid source coverage from primary/authoritative sources.
- Include a **counterpoints / discussion** section that honestly engages the
  strongest objections to your thesis.
- Be **calibrated**: state what the evidence does and does not support.

## Citations (required, uniform format)
- Cite inline as `(S1)`, `(S2)`, … in the article body.
- For **every source you actually cite**, save the fetched page text to
  `<workspace>/sources/S<n>.txt` (e.g. `sources/S1.txt`). One file per distinct
  source, matching the inline number. This lets a reader verify your quotes.
- When you quote a source, copy the wording **verbatim** from the page.
- End the article with a `## 参考文献` list mapping S1, S2, … to title + URL.

## Output
- The finished article: `<workspace>/article.md`.
- Then stop. Your final message = a one-line note of how many sources you cited.
