-- Migration 011: Add market_driver and key_cities to location_margin_config
ALTER TABLE location_margin_config ADD COLUMN IF NOT EXISTS market_driver TEXT;
ALTER TABLE location_margin_config ADD COLUMN IF NOT EXISTS key_cities TEXT;
