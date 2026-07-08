"""V-SEM — S5 semantic retrieval rules (docs/09 §V-SEM, docs/18).

Semantic is an UPGRADE, not a dependency, so these rules are corruption/consistency
guards on the AUDIT surface a pack exposes — never a judgement about relevance:

  V-SEM-01  model pinned (name, revision, weights sha) in every hybrid pack;
            execution deterministic (proven by T-S5-1, enforced by the pin).
  V-SEM-02  every pack names its matcher (hybrid.v1 | keyword.v1) and, when
            hybrid, carries per-EU scores as fixed-6-decimal strings.
  V-SEM-03  degrade-to-keyword is explicit (a warning + keyword.v1), never a
            silent fallback — behavioural, exercised by T-S5-4.
  V-SEM-04  no auto-fulfilment from similarity anywhere: a DocsRequest's
            fulfilled_by is only ever None | "cache" | a DRES id.
  V-SEM-05  clustering only within a document; representatives deterministic —
            behavioural, exercised by T-S5 clustering tests.
"""

from __future__ import annotations

import re
from typing import Any

from ..envelope import Failure

_SIX_DP = re.compile(r"^-?\d+\.\d{6}$")


def check_pack(pack: dict[str, Any]) -> list[Failure]:
    """V-SEM-01 / V-SEM-02: a docs_pack.v2's retrieval block is well-formed.

    A hybrid.v1 pack pins the model (name/revision/weights_sha256) and carries
    per-EU scores serialized as fixed-6-decimal strings; a keyword.v1 pack names
    no model. Applies only to docs_pack.v2 records (v1 is exempt/legacy)."""
    failures: list[Failure] = []
    if pack.get("schema_version") != "docs_pack.v2":
        return failures
    retrieval = pack.get("retrieval")
    if not isinstance(retrieval, dict):
        return [Failure("V-SEM-02", "docs_pack.v2 missing a retrieval block")]

    matcher = retrieval.get("matcher")
    if matcher not in ("hybrid.v1", "keyword.v1"):
        failures.append(Failure("V-SEM-02", f"retrieval.matcher not in {{hybrid.v1,keyword.v1}}: {matcher!r}"))

    model = retrieval.get("model")
    if matcher == "hybrid.v1":
        if not isinstance(model, dict) or not all(
            model.get(k) for k in ("name", "revision", "weights_sha256")
        ):
            failures.append(Failure("V-SEM-01", "hybrid.v1 pack must pin model name/revision/weights_sha256"))
        for sc in retrieval.get("scores", []) or []:
            for key in ("sscore", "kscore"):
                val = sc.get(key)
                if not (isinstance(val, str) and _SIX_DP.match(val)):
                    failures.append(Failure(
                        "V-SEM-02",
                        f"score {sc.get('evidence_id')!r}.{key} must be a fixed-6-decimal string, got {val!r}",
                    ))
    elif matcher == "keyword.v1" and model is not None:
        failures.append(Failure("V-SEM-01", "keyword.v1 pack must NOT pin an embedding model"))
    return failures


def check_no_similarity_fulfillment(requests: list[dict[str, Any]]) -> list[Failure]:
    """V-SEM-04: similarity NEVER auto-fulfills a DocsRequest. A request may only
    be fulfilled by an ingest (a DRES id) or the fingerprint cache ("cache") —
    never by an embedding-similarity match. The request-level cache stays
    fingerprint-only; advisory similar-request leads are prompt-only."""
    failures: list[Failure] = []
    for r in requests:
        fb = r.get("fulfilled_by")
        if fb in (None, "cache"):
            continue
        if isinstance(fb, str) and fb.startswith("DRES-"):
            continue
        failures.append(Failure(
            "V-SEM-04",
            f"request {r.get('request_id')!r} fulfilled_by={fb!r} — only None|cache|DRES- are lawful",
        ))
    return failures
