"""nd brief — the soul command. Deterministic, priority-boxed rendering of the
tree into a bounded briefing; the hard target: an investigation must be
resumable from the brief alone (compaction immunity). Over budget, whole low-
priority sections are dropped first, then items within a section, and every
cut is declared with an honest [truncated: …] marker — never silent."""

from __future__ import annotations

from typing import Any

from . import checks, tree
from .paths import Paths

FRONTIER_STATUSES = ("open", "expanding", "pending", "investigating")


def _line_node(nodes: dict, n: dict[str, Any], max_stmt: int = 140) -> str:
    stmt = n["statement"]
    if len(stmt) > max_stmt:
        stmt = stmt[: max_stmt - 1] + "…"
    path = ">".join(tree.path_of(nodes, n["node_id"])[:-1]) or "root"
    extra = f" [{n['orientation']}]" if n["orientation"] == "adversarial" else ""
    return f"- {n['node_id']} ({n['kind']}, {n['status']}){extra} — {stmt} | at {path}"


def _sections(paths: Paths, session: dict[str, Any]) -> list[tuple[str, list[str]]]:
    nodes = tree.nodes_by_id(paths)
    syns = tree.syntheses(paths)
    latest_syn: dict[str, dict] = {}
    for s in syns:
        latest_syn[s["node_id"]] = s
    referenced_children = {c for s in syns for c in s["based_on"]["children"]}
    budgets = session["budgets"]

    head = [
        f"QUESTION: {session['question']}",
        *( [f"BOUNDARY: {session['boundary_note']}"] if session.get("boundary_note") else [] ),
        (f"BUDGETS: depth {max((tree.depth_of(nodes, i) for i in nodes), default=0)}"
         f"/{budgets['max_depth']} · open claims {tree._open_claims(nodes)}"
         f"/{budgets['max_open_claims']} · nodes {len(nodes)}"),
    ]

    conclusions = []
    for nid in sorted(latest_syn):
        n = nodes.get(nid)
        if n is None or n["kind"] != "viewpoint":
            continue
        s = latest_syn[nid]
        conclusions.append(f"- {nid} [{s['lean']}/{s['confidence']}] {s['summary']}")

    unfolded = []
    for nid in sorted(latest_syn):
        n = nodes.get(nid)
        if n is None or n["kind"] != "claim" or nid in referenced_children:
            continue
        s = latest_syn[nid]
        lean = s["lean"] or "info"
        unfolded.append(f"- {nid} [{lean}/{s['confidence']}] {s['summary']}")

    frontier = [_line_node(nodes, n) for n in
                sorted(nodes.values(), key=lambda x: x["node_id"])
                if n["status"] in FRONTIER_STATUSES]

    stuck = [f"- {n['node_id']} stuck({n['stuck_reason']}): {n['status_note'] or '?'} "
             f"— {n['statement'][:100]}"
             for n in sorted(nodes.values(), key=lambda x: x["node_id"])
             if n["status"] == "stuck"]

    _, soft = checks.run(paths, session)
    warnings = [f"- {w}" for w in soft[:6]]
    if len(soft) > 6:
        warnings.append(f"- [+{len(soft) - 6} more — nd check]")

    return [  # priority order: earlier sections survive truncation longer
        ("SESSION", head),
        ("FRONTIER (act here)", frontier),
        ("CONCLUSIONS (synthesized viewpoints)", conclusions),
        ("ANSWERED, NOT YET FOLDED UP", unfolded),
        ("STUCK", stuck),
        ("DISCIPLINE WARNINGS", warnings),
    ]


_RESERVE = 64  # space held back so the truncation declaration ALWAYS fits


def render(paths: Paths, session: dict[str, Any], max_chars: int = 8000) -> str:
    sections = _sections(paths, session)
    budget = max(max_chars - _RESERVE, 80)
    out: list[str] = []
    used = 0
    dropped = 0

    def fits(text: str) -> bool:
        return used + len(text) + 1 <= budget

    for title, lines in sections:
        if not lines:
            continue
        header = f"\n## {title}"
        if not fits(header):
            dropped += len(lines)
            continue
        out.append(header); used += len(header) + 1
        for i, line in enumerate(lines):
            if not fits(line):
                dropped += len(lines) - i
                break
            out.append(line); used += len(line) + 1
    if dropped:
        out.append(f"\n[truncated: {dropped} lines over budget — nd tree / nd check]")
    return "\n".join(out).strip() + "\n"
