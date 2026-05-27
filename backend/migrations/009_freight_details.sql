-- Migration 009: Add freight details
ALTER TABLE location_margin_config 
ADD COLUMN IF NOT EXISTS distance_km INTEGER DEFAULT 0;

ALTER TABLE daily_rates
ADD COLUMN IF NOT EXISTS loading_cost_per_mt NUMERIC(10, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS fuel_surcharge_pct NUMERIC(5, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS freight_rate_per_mt_km NUMERIC(10, 2) DEFAULT 0.0;
