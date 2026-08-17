"""`project status` must return the documented MSA summary (docs/10 §4), not a
hardcoded null. Guards against the N1 regression found in M4 review."""

from __future__ import annotations

from pathlib import Path

from paperproof import project
from paperproof.paths import Paths


def test_status_includes_real_msa_summary(clock, tmp_path: Path) -> None:
    paths = Paths(tmp_path / "data", "p4-status")
    project.init(paths)
    st = project.status(paths)

    # docs/10 §4: `project status` data includes the MSA summary.
    assert st["msa"] is not None
    assert isinstance(st["msa"], dict)
    # msa_check shape (docs/02 MSA-1..9): a checklist + an all_pass flag.
    assert "all_pass" in st["msa"]
    assert st["msa"]["all_pass"] is False  # empty project cannot satisfy the MSA
    assert isinstance(st["msa"].get("msa"), (list, dict))


def test_status_via_cli_envelope_carries_msa(pp) -> None:
    pp("project", "init", "p4-cli")
    env = pp("--project", "p4-cli", "project", "status")
    assert env["ok"] is True
    assert env["data"]["msa"] is not None
