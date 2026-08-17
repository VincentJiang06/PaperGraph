# Blind review — score deep-research INVESTIGATIONS (not articles)

You are an expert research reviewer. For each **topic** there are **two anonymized
investigation dossiers (A, B)** produced by different processes investigating the **same
hard question**. A dossier records the lines of inquiry pursued, per-line conclusions +
evidence (with verbatim quotes + URLs), dead ends, a root conclusion, and open gaps.
Judge the **quality of the investigation**, not writing style.

## The topics
(Provided in your dispatch message — each has a folder `blinded/<topic>/dossier-A.md`
and `dossier-B.md`.)

## Rubric — integer 1–5 on each dimension (5 = best)
- **coverage** — how many genuinely distinct, relevant lines of inquiry were pursued, including contrarian / non-obvious ones. (Not padding — distinct angles.)
- **depth** — how far each line was pushed: mechanisms, quantities, specific studies — vs surface gestures.
- **adversarial_completeness** — were the leading hypotheses genuinely red-teamed? Was disconfirming evidence sought AND integrated, not strawmanned?
- **grounding** — is every load-bearing claim tied to a specific, verifiable source with a verbatim quote? Could you trust the conclusions without re-doing the research?
- **convergence** — do the many lines integrate into a single calibrated conclusion, or is it a disconnected sprawl of findings?
- **calibration** — are uncertainty, dead ends, and open gaps stated honestly rather than papered over?

## Rules
- **Do NOT reward length or number of lines per se** — a focused, well-grounded, well-integrated investigation beats a sprawling one. Coverage means *distinct useful angles*, not volume.
- **Do NOT try to infer how each dossier was produced.** Judge the content.
- Score each dossier independently; ties allowed. A/B order is arbitrary.
- 1–2 sentence `rationale` per dossier: its single biggest strength and weakness.

## Output — STRICT JSON to the path in your dispatch message
```json
{
  "<topic>": {
    "A": {"coverage":4,"depth":4,"adversarial_completeness":3,"grounding":5,"convergence":4,"calibration":4,"rationale":"…"},
    "B": {...}
  },
  ...
}
```
Read every dossier, score all, write the JSON file, and stop. Final message = one line
confirming the file was written.
