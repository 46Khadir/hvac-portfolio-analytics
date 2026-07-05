"""
Loads the CSV data into a local SQLite database, runs the analysis
queries from sql/analysis_queries.sql, prints the results, and
generates chart images (charts/) summarizing the key findings —
the same aggregates that back the Power BI dashboard.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "hvac_analytics.db"
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)

plt.rcParams.update({"figure.dpi": 120, "font.size": 10})

# ---------------------------------------------------------------------------
# 1. Build the database
# ---------------------------------------------------------------------------
conn = sqlite3.connect(DB_PATH)
conn.executescript((ROOT / "sql" / "schema.sql").read_text())

pd.read_csv(ROOT / "data" / "buildings.csv").to_sql("buildings", conn, if_exists="replace", index=False)
pd.read_csv(ROOT / "data" / "maintenance_logs.csv").to_sql("maintenance_logs", conn, if_exists="replace", index=False)
pd.read_csv(ROOT / "data" / "energy_readings.csv").to_sql("energy_readings", conn, if_exists="replace", index=False)

# ---------------------------------------------------------------------------
# 2. Run each named query and cache the result
# ---------------------------------------------------------------------------
queries = {
    "cost_by_maint_type": """
        SELECT maintenance_type, COUNT(*) AS n_events,
               ROUND(AVG(cost_eur), 2) AS avg_cost_eur,
               ROUND(AVG(downtime_hours), 2) AS avg_downtime_hours
        FROM maintenance_logs GROUP BY maintenance_type ORDER BY avg_cost_eur DESC;
    """,
    "top5_buildings": """
        SELECT b.building_id, b.city, b.sector, b.hvac_type,
               ROUND(SUM(m.cost_eur), 2) AS total_cost_eur, COUNT(*) AS n_events
        FROM maintenance_logs m JOIN buildings b ON b.building_id = m.building_id
        GROUP BY b.building_id ORDER BY total_cost_eur DESC LIMIT 5;
    """,
    "emergency_pct_by_type": """
        SELECT b.hvac_type, COUNT(*) AS total_events,
               SUM(CASE WHEN m.maintenance_type='Emergency' THEN 1 ELSE 0 END) AS emergency_events,
               ROUND(100.0*SUM(CASE WHEN m.maintenance_type='Emergency' THEN 1 ELSE 0 END)/COUNT(*),1) AS emergency_pct
        FROM maintenance_logs m JOIN buildings b ON b.building_id = m.building_id
        GROUP BY b.hvac_type ORDER BY emergency_pct DESC;
    """,
    "cost_by_age": """
        SELECT CASE WHEN 2024-b.install_year<=3 THEN '0-3 years'
                    WHEN 2024-b.install_year<=6 THEN '4-6 years'
                    ELSE '7+ years' END AS age_bracket,
               ROUND(AVG(m.cost_eur),2) AS avg_cost_eur, COUNT(*) AS n_events
        FROM maintenance_logs m JOIN buildings b ON b.building_id = m.building_id
        GROUP BY age_bracket ORDER BY age_bracket;
    """,
    "monthly_energy": """
        SELECT month, ROUND(SUM(energy_kwh),0) AS total_kwh
        FROM energy_readings GROUP BY month ORDER BY month;
    """,
    "energy_intensity_by_sector": """
        SELECT b.sector, ROUND(SUM(e.energy_kwh)/SUM(b.sq_meters),2) AS kwh_per_sqm_total
        FROM energy_readings e JOIN buildings b ON b.building_id = e.building_id
        GROUP BY b.sector ORDER BY kwh_per_sqm_total DESC;
    """,
}

results = {name: pd.read_sql(q, conn) for name, q in queries.items()}

for name, df in results.items():
    print(f"\n--- {name} ---")
    print(df.to_string(index=False))

# ---------------------------------------------------------------------------
# 3. Charts
# ---------------------------------------------------------------------------

# Chart 1 — avg cost by maintenance type
df = results["cost_by_maint_type"]
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.bar(df["maintenance_type"], df["avg_cost_eur"], color=["#2E8B57", "#E8A33D", "#C0392B"])
ax.set_title("Average Cost per Maintenance Event")
ax.set_ylabel("€ per event")
fig.tight_layout()
fig.savefig(CHARTS / "avg_cost_by_maintenance_type.png")
plt.close(fig)

# Chart 2 — emergency % by hvac type
df = results["emergency_pct_by_type"]
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.bar(df["hvac_type"], df["emergency_pct"], color="#C0392B")
ax.set_title("Emergency Call-Out Rate by HVAC System Type")
ax.set_ylabel("% of events that were emergencies")
fig.tight_layout()
fig.savefig(CHARTS / "emergency_rate_by_hvac_type.png")
plt.close(fig)

# Chart 3 — monthly energy trend
df = results["monthly_energy"]
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(df["month"], df["total_kwh"], marker="o", color="#2E5FA3")
ax.set_title("Portfolio-wide Monthly Energy Consumption")
ax.set_ylabel("Total kWh")
ax.tick_params(axis="x", rotation=90)
fig.tight_layout()
fig.savefig(CHARTS / "monthly_energy_trend.png")
plt.close(fig)

# Chart 4 — energy intensity by sector
df = results["energy_intensity_by_sector"]
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.bar(df["sector"], df["kwh_per_sqm_total"], color="#6C5B7B")
ax.set_title("Energy Intensity by Sector")
ax.set_ylabel("kWh / m² (2-year total)")
fig.tight_layout()
fig.savefig(CHARTS / "energy_intensity_by_sector.png")
plt.close(fig)

conn.close()
print(f"\nCharts written to {CHARTS}")
