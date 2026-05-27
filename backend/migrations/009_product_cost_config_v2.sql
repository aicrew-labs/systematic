-- Migration 009: Rebuild product_cost_config table
DROP TABLE IF EXISTS product_cost_config CASCADE;

CREATE TABLE product_cost_config (
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

ALTER TABLE product_cost_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_product_cost_config" ON product_cost_config FOR SELECT USING (true);
CREATE POLICY "public_insert_product_cost_config" ON product_cost_config FOR INSERT WITH CHECK (true);
CREATE POLICY "public_update_product_cost_config" ON product_cost_config FOR UPDATE USING (true);
