# Gate report — m9-s5-semantic-retrieval (attempt 1)

**Result: PASS.** S5 hybrid keyword+embedding retrieval implemented as an OPTIONAL
upgrade that degrades to keyword LOUDLY. FINAL search-program set (Stage C / v2).

## Test counts (gate = default `pytest -q`)

| environment | outcome |
| --- | --- |
| DEFAULT (`.[dev]`, NO semantic deps) | **531 passed, 3 skipped** (the 3 `@pytest.mark.semantic` goldens skip) |
| WITH `.[dev,semantic]` + staged e5 model | **534 passed** (all 3 semantic goldens run) |

Baseline was 510 (@7052ae4 / branch base 345c3a9). Net new: +21 tests
(test_v_sem.py: 16 default + 3 semantic-marked; +2 CLI-envelope params for the two
new `db semantic` commands). No pre-existing assertion weakened or deleted.

- Semantic-marked count: **3** (T-S5-1 determinism, T-S5-2 cross-lingual, T-S5-3 paraphrase).
- Degrade proven by running the full suite in a SECOND venv with the semantic extra
  uninstalled: green, the 3 model tests skip with reason "semantic deps or staged e5 model absent".

## Model (inherited, re-validated with installed onnxruntime 1.27)
- `intfloat/multilingual-e5-small` ONNX, 384-dim; sha256 `ca456c06…6bc8665` (verified).
- inputs `input_ids/attention_mask/token_type_ids`(int64) → `last_hidden_state`; mean-pool+L2-norm, e5 prefixes.
- Re-probe: ZH-query "人工智能对就业的影响" ↔ EN-passage cos 0.90 > unrelated 0.78; byte-identical re-embed True.
- Live hybrid build-pack smoke: cross-lingual EU sscore 0.828734 ranked ABOVE the cake control 0.730122.

## Per-assertion evidence (A48–A51)

- **A48 (V-SEM-01, T-S5-1)** — `db/semantic.py:rebuild` embeds every EU (sorted by id),
  writes `db/semantic/eu_vectors.parquet` (binary float32 blobs, uncompressed, no
  stats) + `model.json` pin. Determinism: two rebuilds ⇒ byte-identical parquet
  (`test_v_sem.py::test_determinism_and_model_pin`, semantic). Session uses
  `intra_op_num_threads=1` (`semantic.py:_session`). Every hybrid pack names the pin
  (`pack.py:assemble_v2` → `retrieval.model`).
- **A49 (T-S5-2/3)** — hybrid math `matcher.py:hybrid_score` (score=0.6·sscore+0.4·kscore,
  include iff sscore≥0.35 OR raw-keyword≥2, order score-desc/id-asc); pack composition
  UNCHANGED `pack.py:assemble_v2` (`selected = requested + matched[:12]`). Cross-lingual
  golden `test_cross_lingual_golden`; paraphrase (zero keyword overlap ≥ τ)
  `test_paraphrase_golden`.
- **A50 (V-SEM-03/04/05, T-S5-4/5)** — degrade: `pack.py:assemble_v2` sets
  `matcher="keyword.v1"` + a `V-SEM-03` warning surfaced in the `docs build-pack`
  envelope (`commands.py:build_pack`; `test_degrade_labeling_keyword_v1_plus_warning`).
  Advisory-only: cache stays fingerprint-only (`cache.py` untouched); `r=REQUESTED ∪ top-12`
  untouched; `v_sem.check_no_similarity_fulfillment` invariant (fulfilled_by ∈
  {None,cache,DRES-}); `test_advisory_only_similarity_never_fulfills`. Clustering:
  `matcher.py:cluster_near_dups` (within-doc cosine≥0.92, rep=longest can_cite_for/tie→lowest id;
  cross-doc NEVER clusters; `test_cluster_near_dups_within_doc_only` + tiebreak/below-τ/no-vectors).
- **A51 (T-S5-back)** — DEFAULT suite green with NO semantic deps (531+3 skip). docs_pack.v2
  round-trips, v1 still readable (`schemas/docs.py:DocsPackV2`, registered;
  `test_docs_pack_v2_round_trip`). V-SEM-01..05 in `validate/registry.py`. verify recomputes
  retrieval ONLY when the pinned model is present, drift → WARNING never a hard fail
  (`verify.py:_semantic_warnings`; drift-warning path smoke-verified).

## Doc-sync (learned from S1's miss)
- `docs/09` §V-SEM (V-SEM-01..05) added in this change.
- `docs/18` synced: model.json dim 768→384 + the actual pin; e5-prefix + pooling + single-thread note; 6-decimal example.
- `docs/10` §4: `docs search --semantic`, `db semantic rebuild|check` rows.

## Escalations
None. CLI/schema deltas stayed within docs/18 (`db semantic rebuild|check`, `docs search --semantic`, `docs_pack.v2`).
