# Artifact contracts

## Run layout

```text
runs/<slug>/
  paper.md
  positions.md
  claims.tsv
  transforms/<claim_id>.py
  metrics/<claim_id>.json
  sources/<claim_id>.txt
  gate_report.md
  eval_bundle/
```

`claims.tsv` uses this exact tab-separated header:

```text
claim_id\tkind\tclaim_text\tvalue\traw_ref\ttransform_or_source\treproduced
```

The Orchestrator writes shared author artifacts. ClaimGrounders may write only
their assigned transform, metric, or source path. Gate scripts own the gate
report; the EvalAggregator owns the merged eval verdict.

## OCR source

`source.json` validates against `schemas/ocr-source.schema.json` and contains:

- schema version, source ID, and provider run ID;
- image width and height;
- fixed provider/action/version, request ID, language, and angle;
- a semantic observation hash;
- ordered elements with stable ID, Unicode text, normalized confidence, and four
  normalized polygon points.

`raw_response.json` is the immutable provider envelope. `manifest.json` binds the
raw, source, and plain-text artifacts by SHA-256 and records request ID and line
count. The exact raw hash belongs in the manifest; the normalized source carries
a semantic hash so detection-order permutations normalize identically.

## Evidence boundary

OCR text is an observed source transcription. It is not a verified fact until a
ClaimGrounder resolves it to the archived source and the orchestrator records the
appropriate claim artifact. Provider request IDs prove extraction events, not the
truth of paper claims.
