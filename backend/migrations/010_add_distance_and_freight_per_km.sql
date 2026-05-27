-- Migration 010: Add distance_from_daman_km to location_margin_config and freight_per_km to daily_rates

-- 1. Add distance_from_daman_km to location_margin_config
ALTER TABLE location_margin_config
ADD COLUMN IF NOT EXISTS distance_from_daman_km FLOAT NOT NULL DEFAULT 0.0;

-- 2. Add freight_per_km to daily_rates
ALTER TABLE daily_rates
ADD COLUMN IF NOT EXISTS freight_per_km FLOAT NOT NULL DEFAULT 20.0;

SELECT 'Migration 010 complete - distance_from_daman_km and freight_per_km columns added successfully.' AS status;
