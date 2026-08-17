# Gate 2 — RIGOR + TRACEABILITY (DVC-backed, executably verified)

**Claim of the gate:** every empirical statement in the paper can be reproduced from raw
data by a re-runnable transform, or verified verbatim against a saved source. The gate
**re-executes** — it does not trust prose. This is the paper's `val_bpb`.

**We do not rebuild reproducibility machinery.** Re-execution, provenance, and (optionally)
data versioning are delegated to **DVC** (`pip install dvc`, invoked as `python3 -m dvc`).
The gate script is a thin wrapper: it runs `dvc repro`, reads the produced numbers, and adds
only the claim↔number comparison, the source-quote check, and the pass rule.

## What counts as an empirical claim
Any sentence whose truth rests on a number, a dated fact, a study result, or a dataset
statistic. If the argument leans on it, it needs a `claims.tsv` row and a way to reproduce it.

## The ledger — `runs/<slug>/claims.tsv` (tab-separated)
```
claim_id  kind  claim_text  value  raw_ref  transform_or_source  reproduced
```
- **kind = `data`** — the value is computed from a dataset (a DVC stage reproduces it).
  - `value` = the number the paper states (e.g. `4.8`, `16.3%`, `239`).
  - `raw_ref` = path under `data/…` (a stage `dep`).
  - `transform_or_source` = `transforms/<claim_id>.py` — a deterministic, no-network script
    that reads the raw data and **writes `metrics/<claim_id>.json` = `{"value": <v>}`** as its
    product. Keep it short; it IS the proof of the number, and its cleaning steps are the
    audit trail (e.g. skipping a missing month).
- **kind = `source`** — the value is a quotation / attributed fact.
  - `value` = the **verbatim quote** (exact substring of the source).
  - `raw_ref` = the source URL.
  - `transform_or_source` = `sources/<claim_id>.txt` — the saved source the quote must appear
    in (whitespace-normalized).
- `reproduced` — leave `?`; the gate is the record.

## The DVC pipeline — `runs/<slug>/dvc.yaml` (one stage per kind=data claim)
```yaml
stages:
  <claim_id>:
    wdir: ../..                                   # run from repo root -> data/ paths resolve
    cmd: python3 runs/<slug>/transforms/<claim_id>.py
    deps:
      - runs/<slug>/transforms/<claim_id>.py      # md5 -> dvc.lock (script provenance)
      - data/<raw file>                           # md5 -> dvc.lock (raw-data provenance)
    metrics:
      - runs/<slug>/metrics/<claim_id>.json:
          cache: false                            # stays a plain, git-readable value
```
`dvc repro` writes `runs/<slug>/dvc.lock`, which records the md5 of every raw dep + transform
+ produced metric: any number in the paper traces to exact bytes + exact script. Run
`python3 -m dvc dag runs/<slug>/dvc.yaml` to see the provenance graph. A humanities-pure
paper with no `data` claims needs **no** dvc.yaml — the gate skips DVC entirely.

## The gate (`python3 gates/rigor_gate.py runs/<slug>`)
1. If any `data` claims exist: `python3 -m dvc repro -f runs/<slug>/dvc.yaml` — force-re-runs
   every transform from raw data (the ship gate never trusts DVC's "unchanged, skipping").
2. For each `data` claim: read `metrics/<claim_id>.json` `value`, compare to the ledger
   `value` (numeric within 1% tolerance, else exact string); attach the dvc.lock provenance.
3. For each `source` claim: check the `value` quote appears (whitespace-normalized,
   case-insensitive) in `sources/<claim_id>.txt`.
4. Write per-claim pass/fail + **reproduce-rate** + provenance into `gate_report.md`; exit
   non-zero if reproduce-rate < 1.0 (ship threshold = 100% — every number reproduces).

### Optional: `--verify-sources` (networked, non-fatal traceability audit)
By default the gate checks a `source` quote against the **saved** `sources/<cid>.txt`, which
proves internal consistency but trusts that the saved text is the real source. Passing
`--verify-sources` re-fetches each `source` claim's `raw_ref` URL and checks the quote is
present there — closing that gap. It is **non-fatal** (publishers 403, paywall, or JS-render,
so a `⚠️` is "could not confirm", not "wrong") and never changes the verdict; the deterministic
offline reproduce-rate stays the ship criterion. Use it as an audit before shipping.

## (Optional) data versioning — deferred, not required
`dvc add data/<file>` would content-address the raw bytes so a reviewer pulls the exact data
each number came from. We do **not** do this to the large real `data/` dir without explicit
sign-off; `dvc repro` + `dvc.lock` already give re-execution and md5 provenance without it.

## Revise on failure
`data` mismatch → the transform doesn't produce the stated number: fix the number to what the
data says, fix the transform, or **drop the claim**. Never "adjust" a number to match prose.
`source` mismatch → the quote isn't in the source: re-fetch, fix the quote, or drop.
