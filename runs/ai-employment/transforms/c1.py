"""c1: mean US unemployment rate (UNRATE), 2020-2025.

Reads the raw FRED series in data/labor/unrate.csv (repo-root relative; the DVC stage
runs this from the repo root), filters to observation years 2020-2025, and writes the
mean monthly rate to metrics/c1.json. Deterministic, no network.
"""
import csv
import json
from pathlib import Path

RUN = Path("runs/ai-employment")

rows, missing = [], []
with open("data/labor/unrate.csv", newline="") as f:
    for r in csv.DictReader(f):
        year = int(r["observation_date"][:4])
        if not (2020 <= year <= 2025):
            continue
        cell = r["UNRATE"].strip()
        if cell == "":  # e.g. 2025-10: BLS release gap. Skip; average over available months.
            missing.append(r["observation_date"])
            continue
        rows.append(float(cell))

mean = sum(rows) / len(rows)
value = round(mean, 1)  # one decimal, as FRED reports the series

(RUN / "metrics").mkdir(exist_ok=True)
(RUN / "metrics" / "c1.json").write_text(json.dumps({"value": value}) + "\n")
print(f"n_months={len(rows)} skipped_missing={missing} mean_unrate_2020_2025={value}")
