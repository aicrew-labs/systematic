-- ============================================================
-- Quote Intelligence — Supabase PostgreSQL Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- ── Products ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    product_type    VARCHAR(100) NOT NULL,
    size_mm         FLOAT,
    size_label      VARCHAR(100) NOT NULL,
    grade           VARCHAR(50),
    unit_of_measure VARCHAR(10) NOT NULL,
    display_name    VARCHAR(200) NOT NULL,
    hsn_code        VARCHAR(20),
    gst_pct         FLOAT DEFAULT 18.0
);

-- ── Customers ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id                 SERIAL PRIMARY KEY,
    name               VARCHAR(200) NOT NULL UNIQUE,
    total_orders       INTEGER DEFAULT 0,
    total_qty_mt       FLOAT DEFAULT 0.0,
    dispatched_qty_mt  FLOAT DEFAULT 0.0,
    is_repeat          BOOLEAN DEFAULT FALSE,
    sales_rep          VARCHAR(100)
);

-- ── Quote History ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS quote_history (
    id              SERIAL PRIMARY KEY,
    quote_date      DATE NOT NULL,
    customer_name   VARCHAR(200) NOT NULL,
    product_type    VARCHAR(100) NOT NULL,
    size_label      VARCHAR(100) NOT NULL,
    grade           VARCHAR(50),
    quantity        FLOAT NOT NULL,
    unit            VARCHAR(10) NOT NULL,
    unit_rate_inr   FLOAT NOT NULL,
    net_amount_inr  FLOAT NOT NULL,
    payment_terms   VARCHAR(50),
    credit_days     INTEGER,
    outcome         VARCHAR(20) NOT NULL,  -- 'won', 'lost', 'pending'
    sales_rep       VARCHAR(100),
    notes           TEXT
);

-- ── Enquiries (from ERP scrape) ──────────────────────────────
CREATE TABLE IF NOT EXISTS enquiries (
    id              SERIAL PRIMARY KEY,
    erp_id          VARCHAR(100),
    enquiry_date    DATE,
    customer_name   VARCHAR(200),
    product_desc    TEXT,
    quantity        FLOAT,
    unit            VARCHAR(20),
    unit_rate_inr   FLOAT,
    status          VARCHAR(50),
    sales_rep       VARCHAR(100),
    remarks         TEXT,
    raw_data        JSONB  -- store original scraped row for reference
);

-- ── FG Inventory ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fg_inventory (
    id              SERIAL PRIMARY KEY,
    snapshot_date   DATE NOT NULL,
    unit_name       VARCHAR(100) NOT NULL,
    product_type    VARCHAR(100) NOT NULL,
    size_label      VARCHAR(100) NOT NULL,
    quantity_mt     FLOAT DEFAULT 0.0,
    inventory_type  VARCHAR(50) NOT NULL  -- 'FG', 'B_Grade', 'Non_Moving', 'WIP'
);

-- ── Machines ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS machines (
    id                       SERIAL PRIMARY KEY,
    unit_name                VARCHAR(100) NOT NULL,
    machine_code             VARCHAR(50) NOT NULL,
    machine_type             VARCHAR(50) NOT NULL,
    product_types            VARCHAR(200),
    min_dia_mm               FLOAT,
    max_dia_mm               FLOAT,
    capacity_mt_per_day      FLOAT,
    current_utilisation_pct  FLOAT DEFAULT 0.0,
    active                   BOOLEAN DEFAULT TRUE
);

-- ── Daily RM Prices ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rm_prices (
    id                SERIAL PRIMARY KEY,
    vendor_name       VARCHAR(100) NOT NULL,
    rm_size_mm        FLOAT NOT NULL,
    rm_grade          VARCHAR(50) NOT NULL,
    rate_per_mt_inr   FLOAT NOT NULL,
    effective_date    DATE NOT NULL
);

-- ── Daily Rates (current day input by user) ──────────────────
CREATE TABLE IF NOT EXISTS daily_rates (
    id              SERIAL PRIMARY KEY,
    rate_date       DATE NOT NULL DEFAULT CURRENT_DATE,
    ms_steel_rate   FLOAT NOT NULL,   -- ₹/MT
    hc_steel_rate   FLOAT NOT NULL,   -- ₹/MT
    zinc_rate       FLOAT NOT NULL,   -- ₹/MT
    entered_by      VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Enable Row Level Security (allow public read) ────────────
ALTER TABLE products        ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers       ENABLE ROW LEVEL SECURITY;
ALTER TABLE quote_history   ENABLE ROW LEVEL SECURITY;
ALTER TABLE enquiries       ENABLE ROW LEVEL SECURITY;
ALTER TABLE fg_inventory    ENABLE ROW LEVEL SECURITY;
ALTER TABLE machines        ENABLE ROW LEVEL SECURITY;
ALTER TABLE rm_prices       ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_rates     ENABLE ROW LEVEL SECURITY;

-- ── Public read policies (HTML dashboard can query) ──────────
CREATE POLICY "Allow public read on products"      ON products      FOR SELECT USING (true);
CREATE POLICY "Allow public read on customers"     ON customers     FOR SELECT USING (true);
CREATE POLICY "Allow public read on quote_history" ON quote_history FOR SELECT USING (true);
CREATE POLICY "Allow public read on enquiries"     ON enquiries     FOR SELECT USING (true);
CREATE POLICY "Allow public read on fg_inventory"  ON fg_inventory  FOR SELECT USING (true);
CREATE POLICY "Allow public read on machines"      ON machines      FOR SELECT USING (true);
CREATE POLICY "Allow public read on rm_prices"     ON rm_prices     FOR SELECT USING (true);
CREATE POLICY "Allow public read on daily_rates"   ON daily_rates   FOR SELECT USING (true);
CREATE POLICY "Allow insert on daily_rates"        ON daily_rates   FOR INSERT WITH CHECK (true);

-- ── Done ─────────────────────────────────────────────────────
SELECT 'Schema created successfully!' AS status;
