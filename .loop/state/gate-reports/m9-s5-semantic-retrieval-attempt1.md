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

---

## Evaluator verdict

**Result: PASS.** Fresh adversarial evaluation of `m9-s5-semantic-retrieval` (HEAD
`de9cd74`). I assumed the work was broken and tried to prove it in BOTH environments;
every probe held. Independently reproduced, not merely re-run of the builder's tests.

### Both environments verified
- **CLEAN venv (true degrade path — NO semantic deps).** Built `/tmp/m9-clean`
  (`uv venv --python 3.12` + `uv pip install -e ".[dev]"`); confirmed
  `import onnxruntime` fails. Full `pytest -q` ⇒ **531 passed, 3 skipped, 0 errors**
  (the 3 `@pytest.mark.semantic` goldens skip with reason "semantic deps or staged e5
  model absent"). Degrade-labeling test green.
- **WITH semantic + staged model.** Repo `.venv` (onnxruntime/numpy/pyarrow/tokenizers
  present) + `PAPERPROOF_SEMANTIC_MODEL_SRC=…/e5-probe`: `pytest -m semantic` ⇒
  **3 passed**. Full `.venv` `pytest -q` ⇒ **534 passed** (goldens auto-run; no skips,
  no regression). Staged `model.onnx` sha256 = `ca456c06…6bc8665` — matches the pin.

### Per-probe (independently driven, not the builder's fixtures)
- **Determinism** — `db semantic rebuild` twice in TWO separate cold CLI processes ⇒
  byte-identical `eu_vectors.parquet` (sha256 `252ba2b0…`). Session pins
  `intra_op_num_threads=1` + `inter_op_num_threads=1`. Scores serialize as fixed-6-dp
  strings. `model.json` pins name/revision=`main`/dim=384/weights_sha256.
- **Cross-lingual is REAL (not a hard-coded fixture)** — live-embedded ZH claim
  "人工智能对就业的影响" vs the EN reinstatement EU ⇒ cos **0.8424 ≥ τ=0.35**, beats the
  cake control (0.6678), raw keyword overlap = **0**. Paraphrase pair sscore **0.8189 ≥ τ**,
  keyword overlap 0. Vectors 384-dim, L2-normalized (‖v‖≈1).
- **Hybrid math (hand-built synthetic vectors)** — score = 0.6·sscore + 0.4·kscore
  exact; include iff (sscore≥0.35 OR raw-keyword≥2): keyword-only=1 EXCLUDED,
  semantic-only (raw 0, cos 1.0) INCLUDED, raw==2 boundary INCLUDED; kscore is min-max
  over candidates; order = score-desc / id-asc. `pack = REQUESTED ∪ top-12` UNCHANGED
  (MATCHED_K=12, requested unconditional; degrade path selects identically to the r3
  keyword `assemble`).
- **Degrade is LOUD, never silent/crash** — `assemble_v2`, `docs build-pack`, and
  `docs search --semantic` with no model ⇒ `matcher="keyword.v1"`, `model=None`, +
  `V-SEM-03` warning in the envelope; persisted pack self-labels keyword.v1.
  `db semantic check` ⇒ exit 0, `deps_available=false` + warning (no crash);
  `db semantic rebuild` ⇒ exit 1 clean DomainError (no traceback).
- **No auto-fulfillment [V-SEM-04]** — cache is fingerprint-only (`fingerprint_hit`
  requires a `DRES-` prefix, so a "cache"-fulfilled request is never itself a source).
  Injected a `fulfilled_by="similarity:0.99"` into a verify-clean project ⇒ `verify`
  HARD-fails (exit 3) citing **V-SEM-04** (a hard invariant, not a warning).
- **Clustering [V-SEM-05]** — within-doc near-dups collapse (rep = longest can_cite_for,
  tie → lowest id); an identical-vector EU in a DIFFERENT doc is NEVER clustered
  (cross-doc corroboration preserved).
- **Weakened-test audit** — `git diff gate/m8-s4 -- tests/` is additive only:
  `test_v_sem.py` (+434 new), `test_cli_envelope.py` (+2 new closed commands),
  `test_rule_coverage.py` (+5 V-SEM entries), `docs_pack.v2.json` fixture (+1). No prior
  assertion loosened; keyword `assemble`/`match`/`fingerprint` intact.
- **Doc-sync** — docs/09 §V-SEM (V-SEM-01..05) present; docs/18 has dim 384, the real
  pin, query/passage prefixes, single-thread note, 6-dp example; docs/10 §4 carries the
  `db semantic rebuild|check` + `docs search --semantic` rows. V-SEM-01..05 registered
  in `validate/registry.py`. Only new schema literal: `docs_pack.v2`. No surface beyond
  docs/18.

### Non-blocking observations (no fix required to tag gate/m9)
- `db/semantic.py:advisory_leads` is implemented but never wired to any caller (dead
  future hook). docs/18 says the advisory use is optional ("the engine MAY attach…"),
  so its absence is conservative and cannot leak similarity into fulfillment — safe.
- `prooftask/builder.py:build_bundle` discards the transient degrade warning string
  (only `docs build-pack` surfaces it), but the persisted `DocsPackV2` still records
  `matcher="keyword.v1"`/`model=None`, so the degrade is never silent — consistent with
  V-SEM-03 which ties the warning to the `docs build-pack` envelope.

Gate PASSES. No defect blocks tagging `gate/m9` (which completes the search program, v2).

— Evaluator (fresh/adversarial), 2026-07-08
