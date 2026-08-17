"""S5 semantic retrieval — hybrid matching, cross-lingual recall (docs/18, §12c).

Two tiers:
  * DEFAULT suite (no `[semantic]` extra needed): the hybrid-scoring MATH runs on
    SYNTHETIC vectors, plus degrade labeling (V-SEM-03), advisory-only
    (V-SEM-04), clustering (V-SEM-05), docs_pack.v2 round-trip, and the V-SEM
    pack rules. These must be green on keyword-only.
  * `@pytest.mark.semantic` tests need the vendored e5 model + onnxruntime; they
    SKIP when absent. Determinism (T-S5-1), cross-lingual (T-S5-2), paraphrase
    (T-S5-3).
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from paperproof import project as project_mod
from paperproof.db import semantic
from paperproof.docsdb import matcher, pack
from paperproof.paths import paths_for
from paperproof.schemas.docs import DocsPackV2
from paperproof.serialize import canonical_bytes
from paperproof.store import jsonl
from paperproof.validate.rules import v_sem

pytestmark = pytest.mark.contract

EVIDENCE_UNITS = "docs/evidence_units.jsonl"

# The staged probe model (see the S5 build brief); an evaluator may instead point
# PAPERPROOF_SEMANTIC_MODEL_SRC at its own copy.
_STAGED = Path(
    "/private/tmp/claude-501/-Users-vince-playground-Paper-Graph/"
    "a09a5a0e-f852-43d0-a8d7-2c395e802ca3/scratchpad/e5-probe"
)


def _model_src() -> Path | None:
    env = os.environ.get("PAPERPROOF_SEMANTIC_MODEL_SRC")
    if env and (Path(env) / "model.onnx").exists():
        return Path(env)
    if (_STAGED / "model.onnx").exists():
        return _STAGED
    return None


_SEMANTIC_READY = semantic.deps_available() and _model_src() is not None


# ---------------------------------------------------------------------------
# synthetic-vector helpers (no model)
# ---------------------------------------------------------------------------


def _eu(eid, doc_id, summary, can_cite, *, quote=None, scope=None):
    return {
        "schema_version": "evidence_unit.v1", "evidence_id": eid, "project_id": "sem-proj",
        "doc_id": doc_id, "location": "p.1", "kind": "paraphrase",
        "quote_or_paraphrase": quote if quote is not None else summary, "summary": summary,
        "support_direction": "supports", "can_cite_for": list(can_cite),
        "cannot_cite_for": ["not this"], "scope": scope or {},
        "extracted_by": "t", "ingested_from": "DRES-001", "created_at": "2026-07-07T00:00:00Z",
    }


# ---------------------------------------------------------------------------
# hybrid scoring MATH on synthetic vectors  (T-S5-back — DEFAULT suite)
# ---------------------------------------------------------------------------


def test_hybrid_score_math_ordering_and_thresholds():
    eus = [
        _eu("EU-1", "D1", "alpha beta gamma", ["alpha beta"]),
        _eu("EU-2", "D2", "delta epsilon", ["delta"]),
        _eu("EU-3", "D3", "zeta theta", ["zeta"]),
    ]
    claim = "alpha beta gamma delta"  # raw keyword: EU-1=3, EU-2=1, EU-3=0
    vecs = {"EU-1": [1.0, 0.0, 0.0], "EU-2": [0.0, 1.0, 0.0], "EU-3": [0.9, 0.1, 0.0]}
    claim_vec = [1.0, 0.0, 0.0]  # cosine: EU-1=1.0, EU-2=0.0, EU-3≈0.994

    included, scores = matcher.hybrid_score(claim, {}, eus, vecs, claim_vec)
    order = [eu["evidence_id"] for _s, eu in included]

    # EU-2 EXCLUDED: sscore 0 < 0.35 AND raw keyword 1 < 2.
    # EU-3 INCLUDED on SEMANTICS ALONE (raw keyword 0) — the paraphrase win.
    assert order == ["EU-1", "EU-3"]
    # score = 0.6*sscore + 0.4*kscore(min-max). EU-1 tops both halves ⇒ 1.0.
    assert scores["EU-1"]["score"] == pytest.approx(1.0)
    # min-max over raw {3,1,0}: EU-1→1.0, EU-2→1/3, EU-3→0.0
    assert scores["EU-1"]["kscore"] == pytest.approx(1.0)
    assert scores["EU-2"]["kscore"] == pytest.approx(1 / 3)
    assert scores["EU-3"]["kscore"] == pytest.approx(0.0)
    assert scores["EU-3"]["sscore"] == pytest.approx(0.994, abs=1e-3)
    assert scores["EU-3"]["raw_kscore"] == 0.0


def test_hybrid_score_clamps_and_alpha_tau_constants():
    # sscore clamps to [0,1]; contract constants are pinned.
    assert matcher.ALPHA == 0.6
    assert matcher.TAU == 0.35
    assert matcher.KEYWORD_RAW_MIN == 2
    eus = [_eu("EU-1", "D1", "x", ["x"])]
    vecs = {"EU-1": [2.0, 0.0]}  # unnormalized; cosine with [1,0] == 1.0 (clamped)
    included, scores = matcher.hybrid_score("q", {}, eus, vecs, [1.0, 0.0])
    assert scores["EU-1"]["sscore"] == pytest.approx(1.0)


def test_hybrid_score_scope_filters_before_scoring():
    eus = [
        _eu("EU-1", "D1", "alpha beta", ["alpha"], scope={"region": "UK"}),
        _eu("EU-2", "D2", "alpha beta", ["alpha"], scope={"region": "US"}),
    ]
    included, _ = matcher.hybrid_score("alpha beta", {"region": "UK"}, eus, {}, None)
    assert [eu["evidence_id"] for _s, eu in included] == ["EU-1"]


def test_degrade_no_vectors_is_keyword_only():
    # keyword.v1 path: no vectors, no claim_vec ⇒ sscore 0 everywhere; only
    # raw-keyword>=2 survives (identical to the docs/04 matcher).
    eus = [
        _eu("EU-1", "D1", "alpha beta gamma", ["alpha"]),  # raw 3
        _eu("EU-2", "D2", "alpha", ["nope"]),  # raw 1
    ]
    included, scores = matcher.hybrid_score("alpha beta gamma", {}, eus, None, None)
    assert [eu["evidence_id"] for _s, eu in included] == ["EU-1"]
    assert scores["EU-1"]["sscore"] == 0.0


# ---------------------------------------------------------------------------
# near-dup clustering  (V-SEM-05 — DEFAULT suite)
# ---------------------------------------------------------------------------


def test_cluster_near_dups_within_doc_only():
    eus = [
        _eu("EU-1", "D1", "s", ["a", "b"]),  # longer can_cite ⇒ representative
        _eu("EU-2", "D1", "s", ["a"]),  # near-dup of EU-1, same doc
        _eu("EU-3", "D2", "s", ["a"]),  # identical vector but DIFFERENT doc
    ]
    vecs = {"EU-1": [1.0, 0.0], "EU-2": [1.0, 0.0], "EU-3": [1.0, 0.0]}
    kept, also = matcher.cluster_near_dups(eus, vecs)
    # EU-1/EU-2 collapse (cos 1.0 ≥ 0.92); EU-3 NEVER clusters across documents.
    assert [e["evidence_id"] for e in kept] == ["EU-1", "EU-3"]
    assert also == {"EU-1": ["EU-2"]}


def test_cluster_rep_tiebreak_lowest_id():
    eus = [
        _eu("EU-5", "D1", "s", ["a"]),  # same can_cite length as EU-2
        _eu("EU-2", "D1", "s", ["a"]),
    ]
    vecs = {"EU-5": [1.0, 0.0], "EU-2": [1.0, 0.0]}
    kept, also = matcher.cluster_near_dups(eus, vecs)
    # tie on can_cite length ⇒ lowest id (EU-2) is the representative.
    assert [e["evidence_id"] for e in kept] == ["EU-2"]
    assert also == {"EU-2": ["EU-5"]}


def test_cluster_below_tau_does_not_collapse():
    eus = [_eu("EU-1", "D1", "s", ["a"]), _eu("EU-2", "D1", "s", ["a"])]
    vecs = {"EU-1": [1.0, 0.0], "EU-2": [0.0, 1.0]}  # cos 0.0 < 0.92
    kept, also = matcher.cluster_near_dups(eus, vecs)
    assert [e["evidence_id"] for e in kept] == ["EU-1", "EU-2"]
    assert also == {}


def test_cluster_no_vectors_never_clusters():
    eus = [_eu("EU-1", "D1", "s", ["a"]), _eu("EU-2", "D1", "s", ["a"])]
    kept, also = matcher.cluster_near_dups(eus, None)  # keyword.v1 ⇒ nothing clusters
    assert [e["evidence_id"] for e in kept] == ["EU-1", "EU-2"]
    assert also == {}


# ---------------------------------------------------------------------------
# docs_pack.v2 round-trip + V-SEM-01/02 pack rules  (DEFAULT suite)
# ---------------------------------------------------------------------------


def test_docs_pack_v2_round_trip():
    p = DocsPackV2(
        pack_id="DOCSPACK-NODE-001", task_id="PT-NODE-001", project_id="sem-proj",
        evidence_units=[], documents_meta=[],
        retrieval={
            "matcher": "hybrid.v1", "model": semantic.model_pin(),
            "alpha": "0.6", "tau": "0.35",
            "scores": [{"evidence_id": "EU-007", "sscore": "0.810000", "kscore": "0.440000"}],
        },
    )
    b1 = canonical_bytes(p)
    b2 = canonical_bytes(DocsPackV2.model_validate_json(b1))
    assert b1 == b2  # dump→parse→dump fixed point
    # v1 stays readable (still registered) — different schema, no retrieval block.
    from paperproof.schemas import REGISTRY

    assert "docs_pack.v1" in REGISTRY and "docs_pack.v2" in REGISTRY


def test_check_pack_hybrid_requires_model_and_six_decimal_scores():
    # missing model pin ⇒ V-SEM-01
    bad_model = {"schema_version": "docs_pack.v2", "pack_id": "P", "task_id": "T",
                 "project_id": "x", "evidence_units": [], "documents_meta": [],
                 "retrieval": {"matcher": "hybrid.v1", "model": None, "alpha": "0.6",
                               "tau": "0.35", "scores": []}}
    assert "V-SEM-01" in [f.rule_id for f in v_sem.check_pack(bad_model)]

    # a non-6-decimal score string ⇒ V-SEM-02
    bad_score = json.loads(json.dumps(bad_model))
    bad_score["retrieval"]["model"] = semantic.model_pin()
    bad_score["retrieval"]["scores"] = [{"evidence_id": "EU-1", "sscore": "0.81", "kscore": "0.440000"}]
    assert "V-SEM-02" in [f.rule_id for f in v_sem.check_pack(bad_score)]


def test_check_pack_keyword_must_not_pin_model():
    kw = {"schema_version": "docs_pack.v2", "pack_id": "P", "task_id": "T",
          "project_id": "x", "evidence_units": [], "documents_meta": [],
          "retrieval": {"matcher": "keyword.v1", "model": semantic.model_pin(),
                        "alpha": "0.6", "tau": "0.35", "scores": []}}
    assert "V-SEM-01" in [f.rule_id for f in v_sem.check_pack(kw)]


def test_check_pack_valid_hybrid_and_keyword_clean():
    good_hybrid = {"schema_version": "docs_pack.v2", "pack_id": "P", "task_id": "T",
                   "project_id": "x", "evidence_units": [], "documents_meta": [],
                   "retrieval": {"matcher": "hybrid.v1", "model": semantic.model_pin(),
                                 "alpha": "0.6", "tau": "0.35",
                                 "scores": [{"evidence_id": "EU-1", "sscore": "0.500000", "kscore": "1.000000"}]}}
    good_keyword = {"schema_version": "docs_pack.v2", "pack_id": "P", "task_id": "T",
                    "project_id": "x", "evidence_units": [], "documents_meta": [],
                    "retrieval": {"matcher": "keyword.v1", "model": None, "alpha": "0.6",
                                  "tau": "0.35", "scores": []}}
    assert v_sem.check_pack(good_hybrid) == []
    assert v_sem.check_pack(good_keyword) == []
    # a docs_pack.v1 record is exempt (legacy, no retrieval block).
    assert v_sem.check_pack({"schema_version": "docs_pack.v1"}) == []


# ---------------------------------------------------------------------------
# degrade labeling via `docs build-pack`  (T-S5-4, V-SEM-03 — DEFAULT suite)
# ---------------------------------------------------------------------------


def test_degrade_labeling_keyword_v1_plus_warning(project, pp):
    """Model absent ⇒ the build envelope carries matcher=keyword.v1 AND a
    V-SEM-03 warning — never a silent fallback."""
    paths = paths_for(pp.tmp_path, "p4-ldi")
    # a minimal graph node + proof task so build-pack has a target (no model built).
    node = {"schema_version": "logic_node.v1", "node_id": "NODE-001", "project_id": "p4-ldi",
            "claim": "Automation displaces some workers.", "scope": {}, "lifecycle_state": "active"}
    jsonl.append(paths.resolve("graph/logic_nodes.jsonl"), node)
    task = {"schema_version": "proof_task.v1", "task_id": "PT-NODE-001", "project_id": "p4-ldi",
            "task_type": "NODE_CHECK", "target": {"node_id": "NODE-001"},
            "context_pack": "proof/context/CTX-NODE-001.json",
            "docs_pack": "docs/docspacks/DOCSPACK-NODE-001.json",
            "output_file": "agent_outputs/proof_results/PT-NODE-001.proof_result.json"}
    jsonl.write_json(paths.resolve("proof/tasks/PT-NODE-001.json"), task)

    env = pp("docs", "build-pack", "--task", "PT-NODE-001")
    assert env["data"]["matcher"] == "keyword.v1"
    assert any("V-SEM-03" in w for w in env["warnings"]), env["warnings"]
    # the written pack is a first-class docs_pack.v2 keyword.v1 pack.
    written = json.loads(paths.resolve("docs/docspacks/DOCSPACK-NODE-001.json").read_text())
    assert written["schema_version"] == "docs_pack.v2"
    assert written["retrieval"]["matcher"] == "keyword.v1"
    assert written["retrieval"]["model"] is None


# ---------------------------------------------------------------------------
# advisory-only: similarity NEVER auto-fulfills  (T-S5-5, V-SEM-04 — DEFAULT)
# ---------------------------------------------------------------------------


def test_advisory_only_similarity_never_fulfills(project, pp):
    """A semantically-similar previously-fulfilled request must NOT fulfill a new
    one — the cache stays fingerprint-only (docs/04 unchanged)."""
    paths = paths_for(pp.tmp_path, "p4-ldi")
    node = {"schema_version": "logic_node.v1", "node_id": "NODE-001", "project_id": "p4-ldi",
            "claim": "Automation displaces workers.", "scope": {}, "lifecycle_state": "active"}
    jsonl.append(paths.resolve("graph/logic_nodes.jsonl"), node)

    # First request fulfilled by an ingest (a DRES id) — a lawful cache source.
    r1 = pp("--project", "p4-ldi", "docs", "request", "--target", "NODE-001",
            "--need", "evidence on automation displacing manufacturing workers",
            "--hint", "BLS automation")
    dr1 = r1["data"]["request_id"]
    # simulate its fulfilment by an ingest
    reqs = paths.resolve("docs/docs_requests.jsonl")
    latest = jsonl.latest_by_id(reqs, "request_id")[dr1]
    jsonl.append(reqs, {**latest, "status": "fulfilled", "fulfilled_by": "DRES-001"})

    # A DIFFERENT-WORDED but semantically-similar new request: different fingerprint
    # ⇒ NOT a cache hit ⇒ opens fresh work. Similarity provided no fulfilment.
    r2 = pp("--project", "p4-ldi", "docs", "request", "--target", "NODE-001",
            "--need", "data on robots eliminating factory jobs", "--hint", "OECD robots")
    assert r2["data"]["status"] == "open"
    assert r2["data"]["fulfilled_by"] is None
    assert r2["data"]["work_item_id"] is not None

    # V-SEM-04 invariant: every request's fulfilled_by ∈ {None, "cache", DRES-*}.
    all_reqs = jsonl.latest_records(reqs, "request_id")
    assert v_sem.check_no_similarity_fulfillment(all_reqs) == []


def test_v_sem_04_flags_unlawful_fulfilled_by():
    bad = [{"request_id": "DR-9", "fulfilled_by": "similarity:0.88"}]
    assert "V-SEM-04" in [f.rule_id for f in v_sem.check_no_similarity_fulfillment(bad)]


def test_verify_clean_with_semantic_sweep(project, pp):
    """`verify` integrates the V-SEM-04 sweep + the warning-only retrieval check
    without a hard fail on a keyword-only (no-model) project."""
    env = pp("--project", "p4-ldi", "verify")
    assert env["ok"] is True


# ---------------------------------------------------------------------------
# model-requiring goldens  (@pytest.mark.semantic — SKIP when model absent)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def semantic_env():
    if not _SEMANTIC_READY:
        pytest.skip("semantic deps or staged e5 model absent")
    root = Path(tempfile.mkdtemp(prefix="pp-sem-"))
    paths = paths_for(root, "sem-proj")
    project_mod.init(paths)
    eus = [
        # EN reinstatement EU — the cross-lingual target.
        _eu("EU-REINSTATE", "DOC-1",
            "Automation displaces some workers, but the reinstatement effect creates "
            "new labor demand in emerging occupations, restoring aggregate employment.",
            ["AI creates new jobs through the reinstatement effect"]),
        # paraphrase EU — ZERO keyword overlap with the paraphrase claim below.
        _eu("EU-PARA", "DOC-2",
            "Reinstatement effect: automation restores aggregate employment as fresh "
            "occupations appear across the economy.",
            ["automation restores employment"]),
        # an unrelated EU — the recall control.
        _eu("EU-UNRELATED", "DOC-3",
            "A traditional recipe for baking a moist chocolate sponge cake with cocoa.",
            ["chocolate cake baking"]),
    ]
    for eu in eus:
        jsonl.append(paths.resolve(EVIDENCE_UNITS), eu)
    prev = os.environ.get("PAPERPROOF_SEMANTIC_MODEL_SRC")
    os.environ["PAPERPROOF_SEMANTIC_MODEL_SRC"] = str(_model_src())
    try:
        semantic.rebuild(paths)
    finally:
        if prev is None:
            os.environ.pop("PAPERPROOF_SEMANTIC_MODEL_SRC", None)
        else:
            os.environ["PAPERPROOF_SEMANTIC_MODEL_SRC"] = prev
    yield paths
    shutil.rmtree(root, ignore_errors=True)


@pytest.mark.semantic
def test_determinism_and_model_pin(semantic_env):
    """T-S5-1: same corpus embedded twice ⇒ byte-identical parquet [V-SEM-01];
    model.json pins name/revision/weights_sha256/dim."""
    paths = semantic_env
    parquet = paths.resolve(semantic.EU_VECTORS)
    first = parquet.read_bytes()
    prev = os.environ.get("PAPERPROOF_SEMANTIC_MODEL_SRC")
    os.environ["PAPERPROOF_SEMANTIC_MODEL_SRC"] = str(_model_src())
    try:
        semantic.rebuild(paths)  # rebuild over the identical corpus
    finally:
        if prev is None:
            os.environ.pop("PAPERPROOF_SEMANTIC_MODEL_SRC", None)
        else:
            os.environ["PAPERPROOF_SEMANTIC_MODEL_SRC"] = prev
    assert parquet.read_bytes() == first  # byte-identical

    mj = json.loads(paths.resolve(semantic.MODEL_JSON).read_text(encoding="utf-8"))
    assert mj["name"] == "intfloat/multilingual-e5-small"
    assert mj["revision"] == semantic.MODEL_REVISION
    assert mj["weights_sha256"] == semantic.WEIGHTS_SHA256
    assert mj["dim"] == 384

    # every vector is L2-normalized (unit norm) and 384-dim.
    import numpy as np

    vecs = semantic.load_vectors(paths)
    assert set(vecs) == {"EU-REINSTATE", "EU-PARA", "EU-UNRELATED"}
    for v in vecs.values():
        assert v.shape == (384,)
        assert float(np.linalg.norm(v)) == pytest.approx(1.0, abs=1e-4)


@pytest.mark.semantic
def test_cross_lingual_golden(semantic_env):
    """T-S5-2: a Chinese topic sentence retrieves the English reinstatement EU
    above τ=0.35, and ranks it above the unrelated control."""
    paths = semantic_env
    vecs = semantic.load_vectors(paths)
    claim = "人工智能对就业的影响"  # "the impact of AI on employment"
    cvec = semantic.embed_claim(paths, claim)

    sim_reinstate = matcher._cosine(cvec, vecs["EU-REINSTATE"])
    sim_unrelated = matcher._cosine(cvec, vecs["EU-UNRELATED"])
    assert sim_reinstate >= matcher.TAU  # above the semantic floor
    assert sim_reinstate > sim_unrelated  # cross-lingual recall beats the control

    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    included, scores = matcher.hybrid_score(claim, {}, eus, vecs, cvec)
    ids = [eu["evidence_id"] for _s, eu in included]
    # the EN EU is INCLUDED despite ZERO keyword overlap with the Chinese claim,
    # and outranks the unrelated control.
    assert "EU-REINSTATE" in ids
    assert scores["EU-REINSTATE"]["raw_kscore"] == 0.0
    assert scores["EU-REINSTATE"]["score"] > scores["EU-UNRELATED"]["score"]


@pytest.mark.semantic
def test_paraphrase_golden(semantic_env):
    """T-S5-3: a paraphrase pair with ZERO keyword overlap scores ≥ τ."""
    paths = semantic_env
    vecs = semantic.load_vectors(paths)
    claim = "reabsorption pace of displaced labour force"
    cvec = semantic.embed_claim(paths, claim)

    eus = {e["evidence_id"]: e for e in jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")}
    # zero keyword overlap between the claim and the paraphrase EU haystack.
    assert matcher.score(claim, eus["EU-PARA"]) == 0
    sscore = matcher._cosine(cvec, vecs["EU-PARA"])
    assert sscore >= matcher.TAU


@pytest.mark.semantic
def test_long_text_truncates_without_crash(semantic_env):
    """F7: an EU whose passage exceeds the model's 512-token positional table
    embeds without crashing ONNX, and re-embeds byte-identically (deterministic
    right-truncation at 512). Before the fix this overran the position input and
    raised inside onnxruntime."""
    import numpy as np

    paths = semantic_env
    # >512 tokens: 900 space-separated words prefixed with the e5 "passage: ".
    long_text = " ".join(f"word{i}" for i in range(900))
    assert len(long_text.split()) > semantic.MAX_TOKENS

    first = semantic.embed_texts(paths, [long_text], semantic.PASSAGE_PREFIX)
    second = semantic.embed_texts(paths, [long_text], semantic.PASSAGE_PREFIX)
    assert first.shape == (1, semantic.EMBED_DIM)
    assert float(np.linalg.norm(first[0])) == pytest.approx(1.0, abs=1e-4)
    # deterministic: same text truncates to the same ids ⇒ identical vector.
    assert np.array_equal(first, second)
