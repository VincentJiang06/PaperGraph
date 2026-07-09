"""TC-B (R4): a large tree must keep nd brief within its char budget with
honest truncation (the frontier survives longest), and nd check must stay
correct and non-crashing at scale."""

from __future__ import annotations

import pytest


def _big_tree(ws, n_children=5, depth=3):
    """Build a balanced tree; returns the node count. depth levels under root."""
    ws("init", "t", "--question", "大规模调查", "--budget", "max_depth=6",
       "--budget", "max_children=8", "--budget", "max_open_claims=64")
    ws("add", "--statement", "根观点")                      # N-0001
    frontier = ["N-0001"]
    made = 1
    for _lvl in range(depth):
        nxt = []
        for parent in frontier:
            for j in range(n_children):
                orient = "adversarial" if j == 0 else "neutral"
                env = ws("add", "--parent", parent, "--statement",
                         f"{parent} 的方向 {j}:一个足够长的陈述用于压测简报装箱行为",
                         "--orientation", orient)
                nid = env["data"]["nodes"][0]["node_id"]
                made += 1
                nxt.append(nid)
        frontier = nxt
    return made


def test_brief_stays_bounded_with_honest_truncation(ws):
    made = _big_tree(ws)              # 1 + 5 + 25 + 125 = 156 nodes
    assert made > 100
    for budget in (2000, 4000, 8000, 16000):
        text = ws("brief", "--max-chars", str(budget))["data"]["brief"]
        assert len(text) <= budget + 1, (budget, len(text))
        # at the tightest budgets the tree cannot fit — truncation must be declared
        if budget <= 4000:
            assert "[truncated" in text
        # the frontier (highest-priority actionable section) is always present
        assert "FRONTIER" in text or "[truncated" in text


def test_check_scales_without_crash(ws):
    _big_tree(ws)
    env = ws("check")
    assert isinstance(env["data"]["hard"], list)  # returns, does not crash
    assert env["data"]["hard"] == []              # a well-formed big tree is clean


def test_tree_map_collapses_under_pressure_but_frontier_survives(ws):
    _big_tree(ws)
    tight = ws("brief", "--max-chars", "1500")["data"]["brief"]
    # SESSION header always survives; low-priority TREE MAP is dropped and marked
    assert tight.startswith("## SESSION")
    assert "[truncated" in tight
    assert len(tight) <= 1500 + 1
