# Cold-resume probe — recover an interrupted investigation from disk only

An investigation into a hard economic question was **interrupted**: the working
context is gone. All you have is what the previous agent persisted to disk. Your
job is to recover the **reasoning state** from that artifact alone, and report how
much survived.

## HARD RULES
- Use **only** the artifact named in your dispatch message.
- **Do NOT read `article.md` or `final.md`** — those are the finished product;
  reading them defeats the test. (If you see them, do not open them.)
- Do **not** do any new web research. This measures what the persisted state
  affords, nothing else.

## What to recover (from the artifact only)
For each aspect, mark a status — `full` / `partial` / `lost` — and give the
specific recovered content (or note what's missing):
- **lines_of_inquiry** — the main viewpoints/sub-questions the investigation pursued.
- **leanings** — the conclusion or lean reached on each line (and the overall thesis).
- **key_figures** — specific quantitative findings / evidence the reasoning rested on.
- **adversarial_lines** — the counter-arguments / rival explanations that were examined.
- **evidence_provenance** — can you tell which source backs which claim, and is it verifiable?
- **next_action** — could you resume the investigation and know exactly what to do next?

## Output — STRICT JSON to the path in your dispatch message
```json
{
  "topic": "T?", "mode": "?",
  "recovered": {
    "lines_of_inquiry": {"status":"full|partial|lost","detail":"…"},
    "leanings": {"status":"…","detail":"…"},
    "key_figures": {"status":"…","detail":"…"},
    "adversarial_lines": {"status":"…","detail":"…"},
    "evidence_provenance": {"status":"…","detail":"…"},
    "next_action": {"status":"…","detail":"…"}
  },
  "overall_recoverability": 0-5,
  "narrative": "≤120 words: could a fresh agent actually continue this investigation, or must it restart?"
}
```
Write the JSON file, then stop. Final message = one line with overall_recoverability.
