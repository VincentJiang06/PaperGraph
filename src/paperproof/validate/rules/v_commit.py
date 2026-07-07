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
    return failures
