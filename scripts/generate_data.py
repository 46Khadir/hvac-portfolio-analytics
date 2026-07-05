"""
Generates a synthetic but realistic HVAC maintenance & energy dataset,
loosely modeled on the kind of data captured across commercial,
healthcare and hospitality HVAC portfolios (sheet metal / fibreglass
ductwork installations, VRF and AHU systems).

Output: data/buildings.csv, data/maintenance_logs.csv, data/energy_readings.csv
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# 1. Buildings (the "portfolio")
# ---------------------------------------------------------------------------
cities = ["Lisbon", "Porto", "Madrid", "Barcelona", "Luanda"]
sectors = ["Healthcare", "Hospitality", "Commercial"]
hvac_types = ["VRF", "AHU", "Split System"]

n_buildings = 24
buildings = pd.DataFrame({
    "building_id": [f"B{100 + i}" for i in range(n_buildings)],
    "city": rng.choice(cities, n_buildings),
    "sector": rng.choice(sectors, n_buildings, p=[0.3, 0.35, 0.35]),
    "hvac_type": rng.choice(hvac_types, n_buildings, p=[0.45, 0.35, 0.2]),
    "sq_meters": rng.integers(800, 18000, n_buildings),
    "install_year": rng.integers(2014, 2024, n_buildings),
})

buildings.to_csv("data/buildings.csv", index=False)

# ---------------------------------------------------------------------------
# 2. Maintenance logs
# ---------------------------------------------------------------------------
maint_types = ["Preventive", "Corrective", "Emergency"]
maint_probs = [0.55, 0.35, 0.10]
base_cost = {"Preventive": 180, "Corrective": 420, "Emergency": 950}
base_downtime = {"Preventive": 0.5, "Corrective": 3.0, "Emergency": 9.0}

rows = []
start = date(2023, 1, 1)
for _, b in buildings.iterrows():
    n_events = rng.integers(15, 60)
    for _ in range(n_events):
        m_type = rng.choice(maint_types, p=maint_probs)
        day_offset = int(rng.integers(0, 730))
        event_date = start + timedelta(days=day_offset)
        cost = max(50, rng.normal(base_cost[m_type], base_cost[m_type] * 0.3))
        downtime = max(0.2, rng.normal(base_downtime[m_type], base_downtime[m_type] * 0.4))
        rows.append({
            "building_id": b["building_id"],
            "date": event_date.isoformat(),
            "maintenance_type": m_type,
            "downtime_hours": round(downtime, 1),
            "cost_eur": round(cost, 2),
            "technician_id": f"T{rng.integers(1, 13):02d}",
        })

maintenance_logs = pd.DataFrame(rows).sort_values(["building_id", "date"])
maintenance_logs.to_csv("data/maintenance_logs.csv", index=False)

# ---------------------------------------------------------------------------
# 3. Monthly energy readings
# ---------------------------------------------------------------------------
months = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
rows = []
for _, b in buildings.iterrows():
    base_kwh = b["sq_meters"] * rng.uniform(6, 11)
    for m in months:
        seasonal = 1.35 if m.month in (6, 7, 8, 12, 1) else 1.0
        noise = rng.normal(1.0, 0.06)
        kwh = base_kwh * seasonal * noise
        rows.append({
            "building_id": b["building_id"],
            "month": m.strftime("%Y-%m"),
            "energy_kwh": round(kwh, 1),
        })

energy_readings = pd.DataFrame(rows)
energy_readings.to_csv("data/energy_readings.csv", index=False)

print("Generated:")
print(f"  buildings.csv          {len(buildings)} rows")
print(f"  maintenance_logs.csv   {len(maintenance_logs)} rows")
print(f"  energy_readings.csv    {len(energy_readings)} rows")
