-- ============================================================
-- Migration 005: Pricing configuration tables
-- Two NEW standalone tables for cost-plus pricing engine.
-- No existing tables are modified.
-- ============================================================

-- ── 1. PRODUCT COST CONFIG ────────────────────────────────────
-- Static lookup table: one row per product category.
-- Defines the cost formula inputs (steel/zinc weights, conversion
-- cost, margin bounds) used to calculate floor price.
-- Edited by admin only — not changed daily.
-- ── Column notes ─────────────────────────────────────────────
--   category_code       : short code used as FK from products table
--                         in a future migration.  e.g. 'MS_FINE'
--   category_name       : human-readable label shown in UI
--   steel_type          : 'MS' (mild steel rate), 'HC' (high-carbon
--                         rate), or 'GI' (also uses zinc).
--                         Determines which rate column is read from
--                         daily_rates when computing floor cost.
--   steel_weight_per_mt : kg of wire rod required to produce 1 MT
--                         of finished product (always > 1000 due to
--                         drawing yield loss).  e.g. 1030 for MS wire.
--   zinc_weight_per_mt  : kg of zinc per MT of finished product.
--                         0 for non-galvanised products (MS, HC).
--   yield_loss_pct      : OPTIONAL.  Informational % loss figure shown
--                         in cost breakdown UI.  Not used in formula
--                         (loss is already baked into steel_weight_per_mt).
--   conversion_cost_per_mt : ₹ per MT: power + labour + overhead.
--   packing_cost_per_mt : OPTIONAL. ₹ per MT standard packing cost.
--                         NULL means packing is entered manually per deal.
--   min_margin_pct      : minimum acceptable margin % (also treated as
--                         the base/default starting margin).
--   max_margin_pct      : maximum allowed margin % (ceiling).
--   volume_adj_json     : JSON array of volume bracket adjustments.
--                         Format: [{"min_mt":0,"max_mt":5,"adj_pct":0.0},
--                                  {"min_mt":5,"max_mt":20,"adj_pct":-0.5},
--                                  {"min_mt":20,"max_mt":null,"adj_pct":-1.5}]
--                         NULL means no volume adjustment applied.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS product_cost_config (
    id                      SERIAL       PRIMARY KEY,
    category_id             VARCHAR(50)  NOT NULL UNIQUE,
    category_name           VARCHAR(100) NOT NULL,
    size_min                FLOAT,
    size_max                FLOAT,
    gsm_kg_per_mt           FLOAT,
    steel_type              VARCHAR(50),
    steel_weight            FLOAT,
    yield_loss_pct          FLOAT,
    min_margin_pct          FLOAT,
    max_margin_pct          FLOAT,
    conversion_process      VARCHAR(100),
    updated_by              VARCHAR(100),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pcc_category_id ON product_cost_config(category_id);

-- RLS
ALTER TABLE product_cost_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_product_cost_config"
    ON product_cost_config FOR SELECT USING (true);
CREATE POLICY "public_insert_product_cost_config"
    ON product_cost_config FOR INSERT WITH CHECK (true);
CREATE POLICY "public_update_product_cost_config"
    ON product_cost_config FOR UPDATE USING (true);


-- ── 2. LOCATION MARGIN CONFIG ─────────────────────────────────
-- Static lookup table: one row per destination region.
-- Captures location-based freight defaults, competitive flags,
-- and margin adjustments applied on top of the floor cost.
-- ── Column notes ─────────────────────────────────────────────
--   location_name       : readable city / zone name. e.g. 'Mumbai'
--   region_id           : short code used in the pricing engine and
--                         UI dropdowns.  e.g. 'MH_WEST', 'GJ_EXPORT'
--   region_name         : longer descriptive name shown in reports.
--   state_code          : 2-letter state abbreviation.  e.g. 'MH', 'GJ'
--   gst_type            : 'IGST' (inter-state) or 'CGST_SGST' (same
--                         state as billing unit).  Informational for now.
--   additional_tax_pct  : any entry tax / LBT / octroi on top of GST.
--                         Applied to (floor_cost + freight) before GST.
--   freight_per_mt      : default ₹ per MT freight for this region.
--                         Can be overridden manually per enquiry.
--   is_competitive      : TRUE = high-competition zone; shown as a
--                         warning badge on the quote screen.
--   margin_adjustment_pct: % to add to (positive) or subtract from
--                         (negative) the base margin for this region.
--                         e.g. -2.0 means "reduce margin by 2% here".
--   notes               : free-text notes visible to admin.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS location_margin_config (
    id                      SERIAL       PRIMARY KEY,
    location_name           VARCHAR(100) NOT NULL,
    region_id               VARCHAR(20)  NOT NULL UNIQUE,
    region_name             VARCHAR(100) NOT NULL,
    state_code              VARCHAR(5),
    gst_type                VARCHAR(15)  NOT NULL DEFAULT 'IGST',  -- 'IGST' | 'CGST_SGST'
    additional_tax_pct      FLOAT        NOT NULL DEFAULT 0.0,
    freight_per_mt          FLOAT        NOT NULL DEFAULT 0.0,
    is_competitive          BOOLEAN      NOT NULL DEFAULT FALSE,
    margin_adjustment_pct   FLOAT        NOT NULL DEFAULT 0.0,
    notes                   TEXT,
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    updated_by              VARCHAR(100),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lmc_region_id    ON location_margin_config(region_id);
CREATE INDEX IF NOT EXISTS idx_lmc_state_code   ON location_margin_config(state_code);
CREATE INDEX IF NOT EXISTS idx_lmc_is_active    ON location_margin_config(is_active);
CREATE INDEX IF NOT EXISTS idx_lmc_competitive  ON location_margin_config(is_competitive);

-- RLS
ALTER TABLE location_margin_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_location_margin_config"
    ON location_margin_config FOR SELECT USING (true);
CREATE POLICY "public_insert_location_margin_config"
    ON location_margin_config FOR INSERT WITH CHECK (true);
CREATE POLICY "public_update_location_margin_config"
    ON location_margin_config FOR UPDATE USING (true);


SELECT 'Migration 005 complete — product_cost_config and location_margin_config created.' AS status;
