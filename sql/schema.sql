-- HVAC Maintenance & Energy Analytics — schema
-- SQLite dialect (portable to PostgreSQL/MySQL with minor type changes)

CREATE TABLE IF NOT EXISTS buildings (
    building_id   TEXT PRIMARY KEY,
    city          TEXT NOT NULL,
    sector        TEXT NOT NULL CHECK (sector IN ('Healthcare', 'Hospitality', 'Commercial')),
    hvac_type     TEXT NOT NULL CHECK (hvac_type IN ('VRF', 'AHU', 'Split System')),
    sq_meters     INTEGER NOT NULL,
    install_year  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS maintenance_logs (
    log_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id        TEXT NOT NULL REFERENCES buildings(building_id),
    date               TEXT NOT NULL,
    maintenance_type   TEXT NOT NULL CHECK (maintenance_type IN ('Preventive', 'Corrective', 'Emergency')),
    downtime_hours     REAL NOT NULL,
    cost_eur           REAL NOT NULL,
    technician_id      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS energy_readings (
    reading_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id    TEXT NOT NULL REFERENCES buildings(building_id),
    month          TEXT NOT NULL,       -- 'YYYY-MM'
    energy_kwh     REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_maint_building ON maintenance_logs(building_id);
CREATE INDEX IF NOT EXISTS idx_energy_building ON energy_readings(building_id);
