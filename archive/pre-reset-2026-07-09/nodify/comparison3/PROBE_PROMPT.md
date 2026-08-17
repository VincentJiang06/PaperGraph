# Cold-resume probe — recover an AGGRESSIVE investigation from disk only

A deliberately aggressive, wide-ranging investigation was **interrupted**: the working
context is gone. All you have is what the previous agent persisted to disk. Recover the
**reasoning state** from that artifact alone and report how much survived. Aggressive
runs are big and sprawling — the question is whether the persisted state still lets a
fresh agent continue, or whether it must restart.

## HARD RULES
- Use **only** the artifact named in your dispatch (tree session, or `log.md`).
- **Do NOT read `dossier.md`** (the finished product) or any `article.md`/`final.md`.
- No new web research. This measures what the persisted state affords.

## What to recover (from the artifact only) — status `full`/`partial`/`lost` each:
- **lines_of_inquiry** — the many lines the aggressive run opened (incl. contrarian/dead).
- **leanings** — the conclusion/lean on each, and the overall thesis.
- **key_figures** — specific quantitative findings the reasoning rested on.
- **adversarial_lines** — the red-team lines and what they found.
- **evidence_provenance** — which source backs which claim; verifiable?
- **next_action** — could you resume and know exactly what to do next?

## Output — STRICT JSON to the path in your dispatch message
```json
{
  "topic":"<T>", "arm":"tree|notree",
  "recovered": {
    "lines_of_inquiry":{"status":"…","detail":"…"},
    "leanings":{"status":"…","detail":"…"},
    "key_figures":{"status":"…","detail":"…"},
    "adversarial_lines":{"status":"…","detail":"…"},
    "evidence_provenance":{"status":"…","detail":"…"},
    "next_action":{"status":"…","detail":"…"}
  },
  "overall_recoverability": 0-5,
  "narrative": "≤120 words: could a fresh agent continue this aggressive investigation, or restart?"
}
```
For the tree arm: `cd` into the workspace and run
`/Users/vince/playground/Paper Graph/.venv/bin/nd brief` first, then drill with
`nd tree`, `nd show <id>`, `nd log`, `nd docs for-node <id>`. Write the JSON, then stop.
