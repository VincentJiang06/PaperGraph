"""Self-test for the eval harness — the eval's own golden test (like runs/_smoke for gates).

Runs offline, asserts the mechanical core computes known outputs. Run: python3 eval/selftest.py
Keep this green when touching harness.py.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import harness  # noqa: E402

ok = True


def check(name: str, cond: bool):
    global ok
    ok = ok and cond
    print(("  ok   " if cond else "  FAIL ") + name)


# --- D1 coverage: K1 engaged in a real paragraph, K2's term absent -> 1/2 ---
positions = [{"id": "K1", "name": "a", "key_terms": ["reinstatement", "Autor"]},
             {"id": "K2", "name": "b", "key_terms": ["zzznevermentioned"]}]
paper = ("# t\n\nA long paragraph that genuinely discusses reinstatement and Autor at length, "
         "well past the two-hundred-character threshold, so it counts as a real engaged "
         "paragraph of argument rather than a passing mention of a keyword somewhere in the "
         "prose of the document.\n\nShort tail.\n")
cov = harness.coverage(paper, positions)
check("coverage = 1/2", cov["rate"] == 0.5)
check("K2 flagged missed", any(m["id"] == "K2" for m in cov["missed"]))

# --- namedrop rejected: term present but only in a sub-threshold paragraph ---
paper_nd = "# t\n\nAutor.\n\nreinstatement\n"
check("namedrop -> 0 coverage", harness.coverage(paper_nd, positions)["rate"] == 0.0)

# --- verdict kill-criteria ---
full = {"total": 2, "covered": [1, 2], "missed": [], "rate": 1.0}
r, _ = harness.verdict(full, 1.0, {"steelman_min": 0})
check("steelman 0 -> REVISE", r == "REVISE")
r, _ = harness.verdict(full, 1.0, {"objection_robust": False})
check("objection not robust -> REVISE", r == "REVISE")
r, _ = harness.verdict(full, 1.0, {"claim_coverage": 0.9})
check("claim-coverage < 1 -> REVISE", r == "REVISE")
r, _ = harness.verdict({"rate": 0.75, "missed": [{"id": "K6"}]}, 1.0, {})
check("coverage < 1 -> REVISE", r == "REVISE")
r, _ = harness.verdict(full, 1.0, {"steelman_min": 2, "objection_robust": True,
                                   "claim_coverage": 1.0, "referee_verdict": "accept"})
check("all clean -> SHIP", r == "SHIP")

print("SELFTEST:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
