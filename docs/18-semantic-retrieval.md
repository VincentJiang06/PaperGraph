# 18 S5 — Semantic Retrieval (hybrid matching, cross-lingual recall)

**Status: ADOPTED / BINDING (Stage C, v2) — docs/00 "Search Program Adoption — S5 Semantic Retrieval" (2026-07-08); worklist docs/11 §12c. Model pin: multilingual-e5-small (onnxruntime, 384-dim). COMPLETES the search program.**

The keyword matcher is deterministic and cheap, but the run showed both failure
modes: it over-matched on period/domain tokens (every pack got all 24 EUs
until the r3 K-cap) and it can only ever under-match paraphrase — "reabsorption
pace" never token-overlaps "reinstatement effect", and the project topic was
framed in Chinese while the literature is English. S5 adds a semantic layer
without surrendering determinism or auditability.

## The embedding index (DERIVED, under `db/semantic/`)

```json
// db/semantic/model.json  (the build pin — multilingual-e5-small ONNX)
{"name": "intfloat/multilingual-e5-small", "revision": "main",
 "dim": 384,
 "weights_sha256": "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"}
```

```text
The model is a PROJECT-PINNED artifact: name+revision+weights hash recorded;
same model + same text ⇒ same vector (fp32, CPU, batch-invariant execution —
onnxruntime with intra_op_num_threads=1 for byte-stability). `db semantic rebuild`
fetches the weights (once) and verifies the sha256, then embeds. Embedding =
mean-pool(last_hidden_state, attention_mask) then L2-normalize; texts carry the
e5 prefixes — "query: " for a claim, "passage: " for an EU (required for
cross-lingual quality). Per EU: normalize(summary + " " + join(can_cite_for));
per claim at query time: normalize(claim). The prefixed input is
DETERMINISTICALLY TRUNCATED at 512 model tokens (v2.1 D9 — the tokenizer enforces
the cap; a longer summary+can_cite_for is truncated to the first 512 tokens
BEFORE embedding, so two runs on the same text always see the same input and
produce byte-identical vectors). Vectors live in
db/semantic/eu_vectors.parquet — derived and rebuildable like all of db/; JSONL
remains the only source of truth. A missing/mismatched model file degrades to
keyword matching, loudly (below), never silently.
```

## Hybrid scoring (replaces the matcher score at pack build)

```text
kscore(EU)  := keyword score per docs/04, min-max normalized over candidates
sscore(EU)  := cosine(claim_vec, eu_vec), clamped to [0,1]
score(EU)   := 0.6·sscore + 0.4·kscore
include EU  iff (sscore ≥ 0.35 OR kscore ≥ 2-tokens-raw)
               AND scope_compatible(EU.scope, target.scope)
order       (score desc, evidence_id asc);  pack = REQUESTED ∪ top-12 (r3 rule
            unchanged — semantic scoring feeds the MATCHED half only)
```

Cross-lingual recall is the model's job (multilingual pin): a Chinese-framed
claim retrieves English EUs by meaning. The τ=0.35 floor and α=0.6 are part of
the contract — changing them is a spec change.

## Near-duplicate clustering (pack hygiene)

```text
Within one document: EUs with cosine ≥ 0.92 cluster; the pack takes one
representative per cluster (longest can_cite_for list; tie → lowest id) and
lists the others as "also: EU-x, EU-y" in documents_meta. Across documents:
never clustered (independent corroboration is signal, not duplication — S3
triangulation depends on it).
```

## Auditability (the pack must remain explainable)

```json
// inside docs_pack.v2
"retrieval": {
  "matcher": "hybrid.v1",
  "model": {"name": "…", "revision": "…", "weights_sha256": "…"},
  "alpha": "0.6", "tau": "0.35",
  "scores": [{"evidence_id": "EU-007", "sscore": "0.810000", "kscore": "0.440000"}]
}
```

Scores serialize as fixed-6-decimal strings (byte-determinism across
platforms). `verify` recomputes retrieval when the pinned model is present and
flags drift as a warning; when absent, packs built with `matcher:"keyword.v1"`
are first-class — semantic is an upgrade, not a dependency. The degrade is LOUD on
the builder path too: `docs build-pack` and the `proof build-tasks` bundle build
surface the "model absent — degraded to keyword.v1" warning in their JSON envelope
`warnings[]` (v2.1 D15/V-SEM-03), so an operator sees it, never a silent fallback.

## What semantics may NOT do (the r2.2 lesson, made permanent)

```text
Similarity NEVER auto-fulfills a DocsRequest. The request-level cache stays
fingerprint-only. The one advisory use: on request creation the engine MAY
attach the top-3 semantically-similar previously-fulfilled requests to the
dispatch prompt as leads ("these earlier searches may overlap") — intelligence
for the worker, never a verdict about sufficiency.
```

## Rules (V-SEM)

```text
V-SEM-01  model pinned (name, revision, weights sha) and recorded in every
          hybrid pack; execution deterministic (same text ⇒ same vector)
V-SEM-02  every pack names its matcher (hybrid.v1 | keyword.v1) and, when
          hybrid, carries per-EU scores; verify recomputes when possible
V-SEM-03  degrade-to-keyword is explicit: pack marked keyword.v1 + a warning
          in the build envelope — never a silent fallback
V-SEM-04  no auto-fulfillment from similarity anywhere (cache, committer,
          critic); advisory leads are prompt-only
V-SEM-05  clustering only within a document; representatives deterministic
```

## Deltas at adoption

```text
CLI      db semantic rebuild|check; docs search gains --semantic
Schemas  docs_pack.v2 (retrieval block); db/semantic/* derived layout
Deps     one pinned local embedding model (offline, no network at inference);
         weights vendored or fetched once and hash-verified
Tests    T-S5-1 determinism: same corpus embedded twice ⇒ identical parquet
         T-S5-2 cross-lingual golden: the ai-jobs Chinese topic sentence
                retrieves the English reinstatement EUs above τ
         T-S5-3 paraphrase golden: "reabsorption pace" ↔ "reinstatement
                effect" EU pair scores ≥ τ with zero keyword overlap
         T-S5-4 fallback labeling; T-S5-5 advisory-only (a similar fulfilled
                request must NOT fulfill a new one)
```
