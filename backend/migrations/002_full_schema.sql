-- ============================================================
-- Migration 002: Full ERP-synced Schema
-- DROP old tables, CREATE new ones with proper FK relationships
-- Run in: Supabase Dashboard → SQL Editor → New Query
-- ⚠️  THIS WILL DELETE ALL EXISTING DATA — run on a fresh start
-- ============================================================

-- Step 1: Drop old tables in dependency order
DROP TABLE IF EXISTS quote_history      CASCADE;
DROP TABLE IF EXISTS enquiries          CASCADE;
DROP TABLE IF EXISTS fg_inventory       CASCADE;
DROP TABLE IF EXISTS machines           CASCADE;
DROP TABLE IF EXISTS customers          CASCADE;
DROP TABLE IF EXISTS products           CASCADE;

-- Drop new tables if they exist from a partial run
DROP TABLE IF EXISTS invoices           CASCADE;
DROP TABLE IF EXISTS sales_orders       CASCADE;
DROP TABLE IF EXISTS manufacturing_units CASCADE;
DROP TABLE IF EXISTS rm_prices          CASCADE;
DROP TABLE IF EXISTS daily_rates        CASCADE;

-- Step 2: Create all tables fresh (paste supabase_schema.sql here)
-- ── 1. PRODUCTS ──────────────────────────────────────────────
CREATE TABLE products (
    id              INTEGER PRIMARY KEY,
    product_type    VARCHAR(100) NOT NULL,
    size_mm         FLOAT,
    size_label      VARCHAR(200) NOT NULL,
    grade           VARCHAR(50),
    unit_of_measure VARCHAR(10)  NOT NULL DEFAULT 'MT',
    display_name    VARCHAR(200) NOT NULL,
    hsn_code        VARCHAR(20),
    gst_pct         FLOAT        NOT NULL DEFAULT 18.0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ── 2. CUSTOMERS ─────────────────────────────────────────────
CREATE TABLE customers (
    id                 INTEGER PRIMARY KEY,
    name               VARCHAR(200) NOT NULL UNIQUE,
    phone              VARCHAR(50),
    company_id         INTEGER,
    total_orders       INTEGER NOT NULL DEFAULT 0,
    total_qty_mt       FLOAT   NOT NULL DEFAULT 0.0,
    dispatched_qty_mt  FLOAT   NOT NULL DEFAULT 0.0,
    is_repeat          BOOLEAN NOT NULL DEFAULT FALSE,
    sales_rep          VARCHAR(100)
);

-- ── 3. MANUFACTURING UNITS ───────────────────────────────────
CREATE TABLE manufacturing_units (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    billing_code  VARCHAR(20),
    location      VARCHAR(200)
);

-- ── 4. ENQUIRIES ─────────────────────────────────────────────
CREATE TABLE enquiries (
    id              SERIAL PRIMARY KEY,
    erp_id          VARCHAR(100),
    enquiry_date    DATE,
    customer_id     INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    customer_name   VARCHAR(200),
    product_id      INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_desc    TEXT,
    prod_category   VARCHAR(100),
    quantity        FLOAT,
    unit            VARCHAR(20),
    price_offered   FLOAT,
    target_price    FLOAT,
    status          VARCHAR(50),
    sales_rep       VARCHAR(100),
    source          VARCHAR(100),
    cust_type       VARCHAR(50),
    remarks         TEXT,
    raw_data        JSONB
);
CREATE INDEX idx_enquiries_erp_id      ON enquiries(erp_id);
CREATE INDEX idx_enquiries_customer_id ON enquiries(customer_id);
CREATE INDEX idx_enquiries_product_id  ON enquiries(product_id);
CREATE INDEX idx_enquiries_date        ON enquiries(enquiry_date);

-- ── 5. SALES ORDERS ──────────────────────────────────────────
CREATE TABLE sales_orders (
    id              SERIAL PRIMARY KEY,
    erp_so_no       VARCHAR(50) NOT NULL,
    erp_do_no       VARCHAR(50),
    erp_enquiry_id  VARCHAR(100),
    order_date      DATE,
    customer_id     INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    customer_name   VARCHAR(200),
    product_id      INTEGER REFERENCES products(id) ON DELETE SET NULL,
    prod_code       VARCHAR(200),
    quantity        FLOAT,
    pending_qty     FLOAT,
    dispatched_qty  FLOAT,
    unit            VARCHAR(20),
    unit_rate       FLOAT,
    freight         VARCHAR(50),
    payment_terms   VARCHAR(500),
    credit_days     INTEGER,
    billing_unit_id INTEGER REFERENCES manufacturing_units(id) ON DELETE SET NULL,
    dispatch_from   VARCHAR(500),
    po_number       VARCHAR(100),
    status          VARCHAR(50),
    sales_rep       VARCHAR(100)
);
CREATE INDEX idx_so_erp_so_no    ON sales_orders(erp_so_no);
CREATE INDEX idx_so_customer_id  ON sales_orders(customer_id);
CREATE INDEX idx_so_product_id   ON sales_orders(product_id);

-- ── 6. INVOICES ───────────────────────────────────────────────
CREATE TABLE invoices (
    id                SERIAL PRIMARY KEY,
    erp_invoice_id    VARCHAR(50) NOT NULL,
    erp_inv_nos       VARCHAR(50),
    erp_so_no         VARCHAR(50),
    erp_do_no         VARCHAR(50),
    invoice_date      DATE,
    due_date          DATE,
    customer_id       INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    customer_name     VARCHAR(200),
    product_id        INTEGER REFERENCES products(id) ON DELETE SET NULL,
    prod_code         VARCHAR(200),
    quantity          FLOAT,
    unit              VARCHAR(20),
    unit_rate         FLOAT,
    freight           VARCHAR(50),
    payment_terms     VARCHAR(500),
    credit_days       INTEGER,
    billing_unit_id   INTEGER REFERENCES manufacturing_units(id) ON DELETE SET NULL,
    dispatch_from     VARCHAR(500),
    po_number         VARCHAR(100),
    po_date           DATE,
    order_status      VARCHAR(50),
    voucher_type      VARCHAR(100),
    cgst              FLOAT,
    sgst              FLOAT,
    igst              FLOAT,
    prod_total        FLOAT,
    total_amount      FLOAT,
    sales_rep         VARCHAR(100),
    outcome           VARCHAR(20) DEFAULT 'won'
);
CREATE INDEX idx_inv_erp_invoice_id ON invoices(erp_invoice_id);
CREATE INDEX idx_inv_customer_id    ON invoices(customer_id);
CREATE INDEX idx_inv_product_id     ON invoices(product_id);
CREATE INDEX idx_inv_so_no          ON invoices(erp_so_no);
CREATE INDEX idx_inv_date           ON invoices(invoice_date);

-- ── 7. FG INVENTORY ──────────────────────────────────────────
CREATE TABLE fg_inventory (
    id              SERIAL PRIMARY KEY,
    snapshot_date   DATE NOT NULL,
    unit_id         INTEGER REFERENCES manufacturing_units(id) ON DELETE SET NULL,
    unit_name       VARCHAR(100),
    product_id      INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_type    VARCHAR(100),
    size_label      VARCHAR(100),
    quantity_mt     FLOAT   NOT NULL DEFAULT 0.0,
    inventory_type  VARCHAR(50) NOT NULL DEFAULT 'FG'
);
CREATE INDEX idx_fg_product_id ON fg_inventory(product_id);
CREATE INDEX idx_fg_unit_id    ON fg_inventory(unit_id);

-- ── 8. MACHINES ───────────────────────────────────────────────
CREATE TABLE machines (
    id                       SERIAL PRIMARY KEY,
    unit_id                  INTEGER REFERENCES manufacturing_units(id) ON DELETE SET NULL,
    unit_name                VARCHAR(100),
    machine_code             VARCHAR(50) NOT NULL,
    machine_type             VARCHAR(50) NOT NULL,
    min_dia_mm               FLOAT,
    max_dia_mm               FLOAT,
    capacity_mt_per_day      FLOAT,
    current_utilisation_pct  FLOAT   NOT NULL DEFAULT 0.0,
    active                   BOOLEAN NOT NULL DEFAULT TRUE
);

-- ── 9. RM PRICES ─────────────────────────────────────────────
CREATE TABLE rm_prices (
    id                SERIAL PRIMARY KEY,
    vendor_name       VARCHAR(100) NOT NULL,
    rm_size_mm        FLOAT NOT NULL,
    rm_grade          VARCHAR(50)  NOT NULL,
    rate_per_mt_inr   FLOAT NOT NULL,
    effective_date    DATE  NOT NULL
);

-- ── 10. DAILY RATES ──────────────────────────────────────────
CREATE TABLE daily_rates (
    id              SERIAL PRIMARY KEY,
    rate_date       DATE        NOT NULL DEFAULT CURRENT_DATE,
    ms_steel_rate   FLOAT       NOT NULL,
    hc_steel_rate   FLOAT       NOT NULL,
    zinc_rate       FLOAT       NOT NULL,
    entered_by      VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── RLS ──────────────────────────────────────────────────────
ALTER TABLE products             ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers            ENABLE ROW LEVEL SECURITY;
ALTER TABLE manufacturing_units  ENABLE ROW LEVEL SECURITY;
ALTER TABLE enquiries            ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_orders         ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices             ENABLE ROW LEVEL SECURITY;
ALTER TABLE fg_inventory         ENABLE ROW LEVEL SECURITY;
ALTER TABLE machines             ENABLE ROW LEVEL SECURITY;
ALTER TABLE rm_prices            ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_rates          ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_products"            ON products            FOR SELECT USING (true);
CREATE POLICY "public_read_customers"           ON customers           FOR SELECT USING (true);
CREATE POLICY "public_read_manufacturing_units" ON manufacturing_units FOR SELECT USING (true);
CREATE POLICY "public_read_enquiries"           ON enquiries           FOR SELECT USING (true);
CREATE POLICY "public_read_sales_orders"        ON sales_orders        FOR SELECT USING (true);
CREATE POLICY "public_read_invoices"            ON invoices            FOR SELECT USING (true);
CREATE POLICY "public_read_fg_inventory"        ON fg_inventory        FOR SELECT USING (true);
CREATE POLICY "public_read_machines"            ON machines            FOR SELECT USING (true);
CREATE POLICY "public_read_rm_prices"           ON rm_prices           FOR SELECT USING (true);
CREATE POLICY "public_read_daily_rates"         ON daily_rates         FOR SELECT USING (true);
CREATE POLICY "public_insert_daily_rates"       ON daily_rates         FOR INSERT WITH CHECK (true);

SELECT 'Migration 002 complete — schema v2 ready!' AS status;
