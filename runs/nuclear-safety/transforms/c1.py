"""c1: nuclear deaths per TWh (OWID, 2021). Reads the shared dataset, writes the metric."""
import csv
import json
from pathlib import Path

RUN = Path("runs/nuclear-safety")
COL = "Deaths per terawatt-hour of energy production"

with open("data/energy/death_rates_per_twh.csv", newline="") as f:
    rates = {r["Entity"]: float(r[COL]) for r in csv.DictReader(f)}

value = rates["Nuclear"]
(RUN / "metrics").mkdir(exist_ok=True)
(RUN / "metrics" / "c1.json").write_text(json.dumps({"value": value}) + "\n")
print(f"nuclear_deaths_per_twh={value}")
