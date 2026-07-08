"""Session directory layout. Everything a session owns lives under
<root>/sessions/<session_id>/ — nothing is written anywhere else."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import UsageError

SESSION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")

NODES = "tree/nodes.jsonl"
SYNTHESES = "tree/syntheses.jsonl"
EVENTS = "tree/events.jsonl"
SESSION = "session.json"
NOTES = "notes"


@dataclass(frozen=True)
class Paths:
    root: Path
    session_id: str

    @property
    def session_dir(self) -> Path:
        return self.root / "sessions" / self.session_id

    def resolve(self, rel: str) -> Path:
        return self.session_dir / rel

    def exists(self) -> bool:
        return (self.session_dir / SESSION).exists()


def paths_for(root: str | Path | None, session_id: str | None) -> Paths:
    root = Path(root or os.environ.get("NODIFY_ROOT") or ".").resolve()
    session_id = session_id or os.environ.get("NODIFY_SESSION") or ""
    if not SESSION_ID_RE.match(session_id):
        raise UsageError([f"invalid or missing session id: {session_id!r} "
                          "(pass --session or set NODIFY_SESSION)"])
    return Paths(root=root, session_id=session_id)
