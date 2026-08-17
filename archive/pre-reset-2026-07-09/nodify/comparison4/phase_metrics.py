"""Capture memory-size + coverage after a phase, for both arms. The crux metric:
does the notree log balloon across phases while the tree's brief (what a fresh agent
must actually read to resume) stays bounded? Appends one row per call to growth.jsonl.

Usage: python3 phase_metrics.py <phase-label>
"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ND = "/Users/vince/playground/Paper Graph/.venv/bin/nd"


def tree_state():
    ws = BASE / "runs" / "tree"
    tdir = ws / "sessions" / "cmp" / "tree"
    def latest(f, key):
        d = {}
        for l in (tdir / f).read_text().splitlines() if (tdir / f).is_file() else []:
            r = json.loads(l); d[r[key]] = r
        return d
    nodes = latest("nodes.jsonl", "node_id")
    didx = ws / "sessions" / "cmp" / "docs" / "index.jsonl"
    docs = len({json.loads(l)["doc_id"] for l in didx.read_text().splitlines()}) if didx.is_file() else 0
    # the brief is what a fresh phase agent must READ to resume — measure its bytes
    brief_bytes = 0
    try:
        out = subprocess.run([ND, "brief", "--root", str(ws), "--session", "cmp"],
                             capture_output=True, text=True, timeout=60)
        brief_bytes = len(out.stdout.encode())
    except Exception:
        pass
    claims = sum(1 for n in nodes.values() if n.get("kind") == "claim")
    return {"nodes": len(nodes), "claims": claims, "docs": docs, "resume_read_bytes": brief_bytes}


def notree_state():
    ws = BASE / "runs" / "notree"
    log = ws / "log.md"
    srcs = ws / "sources"
    return {
        "log_bytes": log.stat().st_size if log.is_file() else 0,
        "sources": len(list(srcs.glob("*"))) if srcs.is_dir() else 0,
        # a fresh phase agent must READ the whole log to resume — that IS its resume cost
        "resume_read_bytes": log.stat().st_size if log.is_file() else 0,
    }


def main(label):
    row = {"phase": label, "tree": tree_state(), "notree": notree_state()}
    with open(BASE / "growth.jsonl", "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    t, n = row["tree"], row["notree"]
    print(f'[{label}] tree: nodes={t["nodes"]} claims={t["claims"]} docs={t["docs"]} '
          f'resume_read={t["resume_read_bytes"]}B | '
          f'notree: log={n["log_bytes"]}B sources={n["sources"]} '
          f'resume_read={n["resume_read_bytes"]}B')


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "?")
