"""V-COMMIT: commit invariants (docs/09).

V-COMMIT-01  input-scoped currency (checked live in the Committer)
V-COMMIT-02  input artifact passed validation (checked live)
V-COMMIT-03  no target frozen (checked live)
V-COMMIT-04  CommitDecision lists every append; replay reproduces post-snapshot
V-COMMIT-05  post-commit graph passes V-GRAPH-01..03
V-COMMIT-06  a proof verdict commits only onto a provable target (checked live)

``verify_commits`` re-runs the replay equality (V-COMMIT-04) over every stored
CommitDecision at rest.
"""

from __future__ import annotations

from ...paths import Paths
from ...store import jsonl
from ..envelope import Failure
from ...committer import replay


GRAPH_FILES = ("graph/logic_nodes.jsonl", "graph/logic_edges.jsonl", "graph/tombstones.jsonl")


def verify_commits(paths: Paths) -> list[Failure]:
    failures: list[Failure] = []
    for cd in jsonl.read_all(paths.resolve("commit/commit_decisions.jsonl")):
        cid = cd["commit_id"]
        try:
            ok = replay.replay_reproduces(paths, cid)
        except AssertionError as exc:
            failures.append(Failure("V-COMMIT-04", f"{cid}: replay error: {exc}"))
            continue
        if not ok:
            failures.append(Failure("V-COMMIT-04", f"{cid}: replay does not reproduce post-snapshot"))

    # Snapshot-EOF check (r3, remaps hostile H10): every graph append must be
    # attributed to a commit. The per-commit replay above covers rows inside
    # each [pre, post] window; a record appended AFTER the latest snapshot
    # belongs to no commit — the lease scan deliberately ignores appends
    # (docs/05 prefix rule), so THIS is where a worker's direct graph append
    # is caught. Current row counts must equal the latest snapshot's.
    snaps = jsonl.read_all(paths.snapshots)
    if snaps:
        latest = snaps[-1]["files"]
        for rel in GRAPH_FILES:
            recorded = (latest.get(rel) or {}).get("rows", 0)
            actual = len(jsonl.read_all(paths.resolve(rel)))
            if actual != recorded:
                failures.append(Failure(
                    "V-COMMIT-04",
                    f"{rel}: {actual} rows on disk vs {recorded} in latest snapshot "
                    f"{snaps[-1]['snapshot_id']} — unattributed append/removal",
                ))
    return failures
