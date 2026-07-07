"""Project storage layout (docs/07).

All state lives under ``<root>/projects/<project_id>/``. This module centralizes
the exact tree so ``project init`` and every reader agree byte-for-byte.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Slug rule for project_id (docs/01 derivation table).
PROJECT_ID_RE = r"^[a-z0-9-]{3,32}$"

# Directories created by `project init` (relative to the project root).
DIRS: tuple[str, ...] = (
    "specs",
    "specs/history",
    "graph",
    "proof",
    "proof/tasks",
    "proof/context",
    "docs",
    "docs/raw",
    "docs/text",
    "docs/docspacks",
    "agent_outputs",
    "agent_outputs/expansions",
    "agent_outputs/proof_results",
    "agent_outputs/docs_results",
    "agent_outputs/prose",
    "agent_notes",
    "queue",
    "commit",
    "freeze",
    "compiler",
    "compiler/prose",
    "audit",
    "db",
)

# Empty canonical JSONL files created by `project init`.
EMPTY_JSONL: tuple[str, ...] = (
    "graph/logic_nodes.jsonl",
    "graph/logic_edges.jsonl",
    "graph/tombstones.jsonl",
    "graph/snapshots.jsonl",
    "proof/proof_results.jsonl",
    "docs/documents.jsonl",
    "docs/evidence_units.jsonl",
    "docs/docs_requests.jsonl",
    "queue/work_items.jsonl",
    "queue/events.jsonl",
    "commit/commit_decisions.jsonl",
    "freeze/frozen_items.jsonl",
    "compiler/dry_runs.jsonl",
    "compiler/draft_maps.jsonl",
    "audit/audit_reports.jsonl",
)

# Empty lock files created by `project init`.
LOCK_FILES: tuple[str, ...] = (
    "queue/.lock",
    "commit/.lock",
)

# The three graph files a snapshot hashes over (docs/07 §Snapshots).
GRAPH_SNAPSHOT_FILES: tuple[str, ...] = (
    "graph/logic_nodes.jsonl",
    "graph/logic_edges.jsonl",
    "graph/tombstones.jsonl",
)


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem locations for one project."""

    root: Path
    project_id: str

    @property
    def project_dir(self) -> Path:
        return self.root / "projects" / self.project_id

    def resolve(self, relpath: str) -> Path:
        return self.project_dir / relpath

    @property
    def paper_spec(self) -> Path:
        return self.resolve("specs/paper_spec.json")

    @property
    def project_contract(self) -> Path:
        return self.resolve("specs/project_contract.json")

    @property
    def snapshots(self) -> Path:
        return self.resolve("graph/snapshots.jsonl")

    def exists(self) -> bool:
        return self.project_dir.is_dir()


def paths_for(root: str | Path, project_id: str) -> Paths:
    return Paths(root=Path(root), project_id=project_id)
