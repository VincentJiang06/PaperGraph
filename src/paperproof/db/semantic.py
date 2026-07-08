"""S5 semantic retrieval — the pinned embedding index (docs/18).

Semantic is an OPTIONAL UPGRADE, never a base dependency. Every entry point here
try-imports the heavy deps (onnxruntime, numpy, pyarrow, tokenizers) and degrades
to keyword matching LOUDLY when they are absent (V-SEM-03) — never a silent
fallback, never a crash on the default install.

The model is a PROJECT-PINNED artifact: name + revision + weights sha256 are
recorded, and ``db semantic rebuild`` verifies the sha before embedding. Same
model + same text ⇒ same vector (fp32, CPU, ``intra_op_num_threads=1`` for
byte-stability — probe-validated deterministic). Vectors live under ``db/semantic/``
— derived and rebuildable like all of ``db/``; JSONL stays the only source of
truth.

Embedding: mean-pool(last_hidden_state, attention_mask) then L2-normalize, with
the e5 prefixes ("query: " for a claim, "passage: " for an EU) — required for
cross-lingual quality (docs/18).
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from ..paths import Paths
from ..textutil import normalize

# --- the project pin (docs/18; probe-validated) ------------------------------

MODEL_NAME = "intfloat/multilingual-e5-small"
MODEL_REVISION = "main"
WEIGHTS_SHA256 = "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"
EMBED_DIM = 384
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "

# Production fetch (offline at inference; fetched once + hash-verified). A fresh
# environment with no staged copy downloads these and verifies the sha.
_HF_BASE = f"https://huggingface.co/{MODEL_NAME}/resolve/{MODEL_REVISION}"
_HF_FILES = {
    "model.onnx": f"{_HF_BASE}/onnx/model.onnx",
    "tokenizer.json": f"{_HF_BASE}/tokenizer.json",
    "config.json": f"{_HF_BASE}/config.json",
}

# derived layout under db/semantic/
SEMANTIC_DIR = "db/semantic"
MODEL_ONNX = "db/semantic/model.onnx"
TOKENIZER_JSON = "db/semantic/tokenizer.json"
CONFIG_JSON = "db/semantic/config.json"
MODEL_JSON = "db/semantic/model.json"
EU_VECTORS = "db/semantic/eu_vectors.parquet"

EVIDENCE_UNITS = "docs/evidence_units.jsonl"

# --- dependency availability -------------------------------------------------


def deps_available() -> bool:
    """True iff the `[semantic]` extra is importable. The whole hybrid path is
    gated on this; when False, callers degrade to keyword.v1 (V-SEM-03)."""
    try:  # pragma: no cover - trivial import probe
        import numpy  # noqa: F401
        import onnxruntime  # noqa: F401
        import pyarrow  # noqa: F401
        from tokenizers import Tokenizer  # noqa: F401

        return True
    except Exception:
        return False


def model_pin() -> dict[str, str]:
    """The pin recorded in every hybrid pack's retrieval.model block (V-SEM-01)."""
    return {"name": MODEL_NAME, "revision": MODEL_REVISION, "weights_sha256": WEIGHTS_SHA256}


# --- model provisioning (fetch + hash-verify) --------------------------------


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _model_src_dir() -> Optional[Path]:
    """A local directory to COPY the model from instead of downloading — the
    tests point this at the staged probe copy; production leaves it unset and
    fetches from the HF URL."""
    src = os.environ.get("PAPERPROOF_SEMANTIC_MODEL_SRC")
    if src and Path(src).is_dir():
        return Path(src)
    return None


def _provision_from_dir(src: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in ("model.onnx", "tokenizer.json", "config.json"):
        s = src / name
        if not s.exists():
            continue
        d = dst_dir / name
        if d.exists():
            continue
        # hardlink when possible (instant, no 470MB duplicate); copy across devices.
        try:
            os.link(s, d)
        except OSError:
            shutil.copyfile(s, d)


def _provision_from_hf(dst_dir: Path) -> None:  # pragma: no cover - network path
    import urllib.request

    dst_dir.mkdir(parents=True, exist_ok=True)
    for name, url in _HF_FILES.items():
        d = dst_dir / name
        if d.exists():
            continue
        with urllib.request.urlopen(url) as resp, open(d, "wb") as fh:
            shutil.copyfileobj(resp, fh)


def ensure_model(paths: Paths) -> None:
    """Guarantee ``db/semantic/model.onnx`` (+ tokenizer) present and sha-verified.

    If absent or the hash does not match the pin, provision from the staged local
    dir (tests) or the HF URL (prod), then verify the sha256 — a mismatch raises
    rather than embedding with the wrong weights (V-SEM-01 integrity gate)."""
    from ..errors import DomainError

    dst_dir = paths.resolve(SEMANTIC_DIR)
    onnx = paths.resolve(MODEL_ONNX)
    tok = paths.resolve(TOKENIZER_JSON)

    needs = (not onnx.exists()) or (not tok.exists()) or (_sha256_file(onnx) != WEIGHTS_SHA256)
    if needs:
        src = _model_src_dir()
        if src is not None:
            _provision_from_dir(src, dst_dir)
        else:
            _provision_from_hf(dst_dir)

    if not onnx.exists():
        raise DomainError(["semantic model.onnx could not be provisioned (set PAPERPROOF_SEMANTIC_MODEL_SRC or allow network)"])
    got = _sha256_file(onnx)
    if got != WEIGHTS_SHA256:
        raise DomainError([f"semantic model weights sha256 mismatch: got {got}, want {WEIGHTS_SHA256}"])
    if not tok.exists():
        raise DomainError(["semantic tokenizer.json missing next to model.onnx"])


def model_present(paths: Paths) -> bool:
    """Cheap presence check for the hybrid decision at pack build (no re-hash of
    the 470MB weights — the sha is the integrity gate at rebuild/check time; here
    we trust the recorded model.json pin, which lives under derived ``db/``).

    True iff the onnx weights + tokenizer + a pin-matching model.json all exist."""
    if not deps_available():
        return False
    if not paths.resolve(MODEL_ONNX).exists() or not paths.resolve(TOKENIZER_JSON).exists():
        return False
    mj = paths.resolve(MODEL_JSON)
    if not mj.exists():
        return False
    try:
        import json

        rec = json.loads(mj.read_text(encoding="utf-8"))
    except Exception:
        return False
    return rec.get("weights_sha256") == WEIGHTS_SHA256


# --- embedding session (cached per resolved model path) ----------------------

_SESSIONS: dict[str, Any] = {}
_TOKENIZERS: dict[str, Any] = {}


def _session(paths: Paths):
    import onnxruntime as ort

    key = str(paths.resolve(MODEL_ONNX))
    sess = _SESSIONS.get(key)
    if sess is None:
        so = ort.SessionOptions()
        # single-thread fp32 CPU => byte-stable embeddings (docs/18; probe-proven).
        so.intra_op_num_threads = 1
        so.inter_op_num_threads = 1
        sess = ort.InferenceSession(key, sess_options=so, providers=["CPUExecutionProvider"])
        _SESSIONS[key] = sess
    return sess


# e5's positional table is 512; a longer sequence overruns the ONNX position
# input and crashes (F7 — confirmed on a >512-token EU). Deterministic truncation
# at 512 keeps the model in-range; the same text always truncates to the same
# ids, so re-embedding stays byte-identical (V-SEM-01).
MAX_TOKENS = 512


def _tokenizer(paths: Paths):
    from tokenizers import Tokenizer

    key = str(paths.resolve(TOKENIZER_JSON))
    tok = _TOKENIZERS.get(key)
    if tok is None:
        tok = Tokenizer.from_file(key)
        # deterministic right-truncation at the model's 512-token limit (F7).
        tok.enable_truncation(max_length=MAX_TOKENS)
        _TOKENIZERS[key] = tok
    return tok


def embed_texts(paths: Paths, texts: list[str], prefix: str):
    """Return an (n, 384) float32 L2-normalized embedding matrix for ``texts``
    (each prepended with the e5 ``prefix``). One sequence at a time so padding
    never perturbs a vector (batch-invariant determinism)."""
    import numpy as np

    sess = _session(paths)
    tok = _tokenizer(paths)
    input_names = {i.name for i in sess.get_inputs()}
    out = np.zeros((len(texts), EMBED_DIM), dtype=np.float32)
    for row, text in enumerate(texts):
        enc = tok.encode(prefix + text)
        ids = np.array([enc.ids], dtype=np.int64)
        mask = np.array([enc.attention_mask], dtype=np.int64)
        feeds = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in input_names:
            feeds["token_type_ids"] = np.zeros_like(ids)
        last = sess.run(None, feeds)[0][0]  # (seq, 384)
        m = mask[0][:, None].astype(np.float32)
        pooled = (last * m).sum(0) / max(float(m.sum()), 1.0)
        norm = float(np.linalg.norm(pooled))
        out[row] = (pooled / (norm + 1e-9)).astype(np.float32)
    return out


def embed_claim(paths: Paths, claim: str):
    """The query-side vector for a target claim: normalize + "query: " prefix."""
    return embed_texts(paths, [normalize_claim_text(claim)], QUERY_PREFIX)[0]


def normalize_eu_text(eu: dict[str, Any]) -> str:
    """docs/18: per EU embed normalize(summary + " " + join(can_cite_for))."""
    can = " ".join(eu.get("can_cite_for", []) or [])
    return normalize((eu.get("summary", "") or "") + " " + can)


def normalize_claim_text(claim: str) -> str:
    """docs/18: per claim embed normalize(claim) at query time."""
    return normalize(claim or "")


# --- eu_vectors.parquet (derived, deterministic, gitignored) -----------------
#
# One row per EU: evidence_id (string) + a raw float32[384] blob. Sorted by
# evidence_id, uncompressed, no statistics/timestamps ⇒ same corpus embedded
# twice yields a BYTE-IDENTICAL parquet [V-SEM-01].


def _write_vectors(paths: Paths, ids: list[str], mat) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    blobs = [mat[i].tobytes() for i in range(len(ids))]
    table = pa.table(
        {"evidence_id": pa.array(ids, type=pa.string()),
         "vector": pa.array(blobs, type=pa.binary(EMBED_DIM * 4))}
    )
    dst = paths.resolve(EU_VECTORS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, str(dst), compression="none", write_statistics=False)


def load_vectors(paths: Paths):
    """Return {evidence_id: np.float32[384]} from the parquet, or {} when absent."""
    p = paths.resolve(EU_VECTORS)
    if not p.exists():
        return {}
    import numpy as np
    import pyarrow.parquet as pq

    table = pq.read_table(str(p))
    ids = table.column("evidence_id").to_pylist()
    blobs = table.column("vector").to_pylist()
    return {i: np.frombuffer(b, dtype=np.float32) for i, b in zip(ids, blobs)}


# --- rebuild / check ---------------------------------------------------------


def rebuild(paths: Paths) -> dict[str, Any]:
    """`db semantic rebuild` (docs/18): ensure+verify the pinned model, embed every
    EvidenceUnit, and (re)write eu_vectors.parquet + model.json. Derived and
    idempotent — same corpus ⇒ identical parquet [V-SEM-01]."""
    from ..errors import DomainError
    from ..store import jsonl

    if not paths.project_dir.exists():
        raise DomainError([f"project not found: {paths.project_id}"])
    if not deps_available():
        raise DomainError(["semantic deps absent: install `.[semantic]` (onnxruntime, numpy, pyarrow, tokenizers)"])

    ensure_model(paths)

    eus = jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id")
    eus = sorted(eus, key=lambda e: e["evidence_id"])
    ids = [e["evidence_id"] for e in eus]
    if ids:
        mat = embed_texts(paths, [normalize_eu_text(e) for e in eus], PASSAGE_PREFIX)
    else:
        import numpy as np

        mat = np.zeros((0, EMBED_DIM), dtype=np.float32)
    _write_vectors(paths, ids, mat)

    model_json = {
        "name": MODEL_NAME, "revision": MODEL_REVISION,
        "weights_sha256": WEIGHTS_SHA256, "dim": EMBED_DIM,
    }
    from ..store import jsonl as _jsonl

    _jsonl.write_json(paths.resolve(MODEL_JSON), model_json)
    return {
        "matcher": "hybrid.v1", "model": model_json,
        "eu_count": len(ids), "vectors_path": EU_VECTORS,
    }


def check(paths: Paths) -> dict[str, Any]:
    """`db semantic check` (docs/18): report present/hash-match, never a mutation.
    Reports whether deps + weights + tokenizer + vectors are present and whether
    the on-disk weights sha matches the pin."""
    import json

    from ..store import jsonl

    onnx = paths.resolve(MODEL_ONNX)
    onnx_present = onnx.exists()
    weights_match = bool(onnx_present) and _sha256_file(onnx) == WEIGHTS_SHA256
    vectors = paths.resolve(EU_VECTORS)
    vectors_present = vectors.exists()
    eu_count = None
    if vectors_present:
        try:
            eu_count = len(load_vectors(paths))
        except Exception:
            eu_count = None
    model_json = None
    if paths.resolve(MODEL_JSON).exists():
        try:
            model_json = json.loads(paths.resolve(MODEL_JSON).read_text(encoding="utf-8"))
        except Exception:
            model_json = None
    live_eu = len(jsonl.latest_records(paths.resolve(EVIDENCE_UNITS), "evidence_id"))
    warnings: list[str] = []
    if not deps_available():
        warnings.append("semantic deps absent: retrieval degrades to keyword.v1")
    if onnx_present and not weights_match:
        warnings.append("semantic model weights sha256 does NOT match the pin (drift)")
    if vectors_present and eu_count is not None and eu_count != live_eu:
        warnings.append(f"eu_vectors covers {eu_count} EUs but {live_eu} exist — run `db semantic rebuild`")
    return {
        "deps_available": deps_available(),
        "model_present": onnx_present,
        "weights_match": weights_match,
        "tokenizer_present": paths.resolve(TOKENIZER_JSON).exists(),
        "vectors_present": vectors_present,
        "vectors_eu_count": eu_count,
        "live_eu_count": live_eu,
        "pin": model_pin(),
        "model_json": model_json,
        "warnings": warnings,
    }


# --- advisory-only similar-request leads (V-SEM-04; prompt-only) -------------


def advisory_leads(paths: Paths, need: str, hints: list[str] | None, k: int = 3) -> list[dict[str, Any]]:
    """Top-k semantically-similar PREVIOUSLY-FULFILLED requests as dispatch LEADS
    (docs/18): intelligence for the worker, NEVER a verdict about sufficiency.

    This is advisory only — it is never consulted by the cache or the committer;
    similarity NEVER auto-fulfills a DocsRequest (V-SEM-04). Degrades to [] when
    deps/model are absent (keyword.v1 dispatch carries no leads)."""
    if not model_present(paths):
        return []
    import numpy as np

    from ..store import jsonl

    fulfilled = [
        r for r in jsonl.latest_records(paths.resolve("docs/docs_requests.jsonl"), "request_id")
        if r.get("status") == "fulfilled" and str(r.get("fulfilled_by") or "").startswith("DRES-")
    ]
    if not fulfilled:
        return []
    query_text = normalize((need or "") + " " + " ".join(hints or []))
    qv = embed_texts(paths, [query_text], QUERY_PREFIX)[0]
    scored: list[tuple[float, dict[str, Any]]] = []
    for r in fulfilled:
        rt = normalize((r.get("need", "") or "") + " " + " ".join(r.get("search_hints", []) or []))
        rv = embed_texts(paths, [rt], QUERY_PREFIX)[0]
        scored.append((float(np.dot(qv, rv)), r))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["request_id"]))
    return [
        {"request_id": r["request_id"], "similarity": f"{sim:.6f}", "need": r.get("need", "")}
        for sim, r in scored[:k]
    ]
