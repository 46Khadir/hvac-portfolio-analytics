-- ============================================================
-- HVAC Maintenance & Energy Analytics — analysis queries
-- ============================================================

-- 1. Average cost and downtime by maintenance type
SELECT
    maintenance_type,
    COUNT(*)                       AS n_events,
    ROUND(AVG(cost_eur), 2)        AS avg_cost_eur,
    ROUND(AVG(downtime_hours), 2)  AS avg_downtime_hours
FROM maintenance_logs
GROUP BY maintenance_type
ORDER BY avg_cost_eur DESC;

-- 2. Top 5 buildings by total maintenance spend
SELECT
    b.building_id,
    b.city,
    b.sector,
    b.hvac_type,
    ROUND(SUM(m.cost_eur), 2) AS total_cost_eur,
    COUNT(*)                  AS n_events
FROM maintenance_logs m
JOIN buildings b ON b.building_id = m.building_id
GROUP BY b.building_id
ORDER BY total_cost_eur DESC
LIMIT 5;

-- 3. Emergency-call ratio by HVAC system type
-- (share of maintenance events that were emergencies — a proxy for
--  reliability / preventive-maintenance effectiveness by system type)
SELECT
    b.hvac_type,
    COUNT(*) AS total_events,
    SUM(CASE WHEN m.maintenance_type = 'Emergency' THEN 1 ELSE 0 END) AS emergency_events,
    ROUND(100.0 * SUM(CASE WHEN m.maintenance_type = 'Emergency' THEN 1 ELSE 0 END) / COUNT(*), 1) AS emergency_pct
FROM maintenance_logs m
JOIN buildings b ON b.building_id = m.building_id
GROUP BY b.hvac_type
ORDER BY emergency_pct DESC;

-- 4. Maintenance cost per building age bracket
-- (older installs vs newer installs — does age correlate with cost?)
SELECT
    CASE
        WHEN 2024 - b.install_year <= 3  THEN '0-3 years'
        WHEN 2024 - b.install_year <= 6  THEN '4-6 years'
        ELSE '7+ years'
    END AS age_bracket,
    ROUND(AVG(m.cost_eur), 2) AS avg_cost_eur,
    COUNT(*) AS n_events
FROM maintenance_logs m
JOIN buildings b ON b.building_id = m.building_id
GROUP BY age_bracket
ORDER BY age_bracket;

-- 5. Monthly energy consumption trend across the whole portfolio
SELECT
    month,
    ROUND(SUM(energy_kwh), 0) AS total_kwh
FROM energy_readings
GROUP BY month
ORDER BY month;

-- 6. Energy intensity (kWh per m²) by sector — normalizes for building size
SELECT
    b.sector,
    ROUND(SUM(e.energy_kwh) / SUM(b.sq_meters), 2) AS kwh_per_sqm_total
FROM energy_readings e
JOIN buildings b ON b.building_id = e.building_id
GROUP BY b.sector
ORDER BY kwh_per_sqm_total DESC;
