#!/usr/bin/env python3
"""Deterministic routing oracle for PaperGraph trigger regression tests."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


_EXPLICIT = re.compile(r"\bpaper\s*graph\b", re.IGNORECASE)
_PAPER_OUTCOME = re.compile(
    r"(?:\b(?:research\s+paper|finished(?:,\s*|\s+)(?:auditable\s+)?paper|evidence[- ]backed\s+paper|turn\s+.+\s+into\s+(?:an?\s+)?paper)\b|(?:研究论文|完成.{0,8}论文|证据.{0,4}论文))",
    re.IGNORECASE,
)
_WORKFLOW_SIGNAL = re.compile(
    r"(?:\b(?:auditable|evidence[- ]backed|map\s+the\s+debate|ground\s+the\s+claims|held[- ]out|scanned\s+(?:papers|sources)|source\s+bundle)\b|(?:可审计|证据|扫描|来源包|主张|门槛|评估))",
    re.IGNORECASE,
)
_ADJACENT_ONLY = re.compile(
    r"(?:\b(?:plain\s+text\s+only|fact[- ]check|copy\s+edit|proofread|implement\s+(?:a|an|the)?\s*\w*|add\s+unit\s+tests)\b|(?:只.{0,6}OCR|事实核查|润色|校对|实现.{0,8}代码|单元测试))",
    re.IGNORECASE,
)


def classify_request(prompt: str) -> dict[str, Any]:
    """Classify a prompt without calling a model or inspecting project state."""

    normalized = " ".join(prompt.split())
    explicit = bool(_EXPLICIT.search(normalized))
    full_paper = bool(_PAPER_OUTCOME.search(normalized))
    workflow = bool(_WORKFLOW_SIGNAL.search(normalized))
    adjacent = bool(_ADJACENT_ONLY.search(normalized))
    activate = explicit or (full_paper and workflow and not adjacent)
    if not activate:
        return {"activate": False, "route": "narrower_tool", "phases": []}
    return {
        "activate": True,
        "route": "papergraph",
        "phases": [
            "scope",
            "ocr",
            "cartography",
            "parallel_author_wave",
            "claim_grounding",
            "author_gates",
            "held_out_eval",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify a PaperGraph trigger prompt")
    parser.add_argument("prompt", nargs="+")
    args = parser.parse_args(argv)
    print(json.dumps(classify_request(" ".join(args.prompt)), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
