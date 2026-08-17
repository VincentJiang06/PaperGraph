"""c1 (smoke): AI-exposure share of postings. Reads shared repo-root data/, writes metric."""
import csv
import json
from pathlib import Path

RUN = Path("runs/_smoke")

with open("data/_smoke_postings.csv", newline="") as f:
    rows = list(csv.DictReader(f))

share = sum(int(r["ai_exposed"]) for r in rows) / len(rows)

(RUN / "metrics").mkdir(exist_ok=True)
(RUN / "metrics" / "c1.json").write_text(json.dumps({"value": f"{share:.0%}"}) + "\n")
print(f"share={share:.0%}")  # -> 40%
