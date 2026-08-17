"""c3: how many times deadlier coal is than nuclear per TWh (a derived ratio).

A two-row transform: reads both rates from the shared dataset and divides. Reproduces the
paper's "coal is over 800x deadlier than nuclear" claim from raw data, not by hand.
"""
import csv
import json
from pathlib import Path

RUN = Path("runs/nuclear-safety")
COL = "Deaths per terawatt-hour of energy production"

with open("data/energy/death_rates_per_twh.csv", newline="") as f:
    rates = {r["Entity"]: float(r[COL]) for r in csv.DictReader(f)}

value = round(rates["Coal"] / rates["Nuclear"])
(RUN / "metrics").mkdir(exist_ok=True)
(RUN / "metrics" / "c3.json").write_text(json.dumps({"value": value}) + "\n")
print(f"coal_over_nuclear_ratio={value}")
