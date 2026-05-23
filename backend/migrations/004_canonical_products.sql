-- ============================================================
-- Migration 004: Rebuild products as canonical catalog
-- - Source of truth shifts from RMS to transactions
-- - Products table holds canonical SKUs only (~200 rows expected)
-- - New product_rms_specs table holds RMS variants as enrichment
-- ============================================================

-- Step 1: Drop FK constraints that reference products.id
-- (We'll re-add them after the new products table is built and re-linked.)
ALTER TABLE invoices       DROP CONSTRAINT IF EXISTS invoices_product_id_fkey;
ALTER TABLE sales_orders   DROP CONSTRAINT IF EXISTS sales_orders_product_id_fkey;
ALTER TABLE enquiries      DROP CONSTRAINT IF EXISTS enquiries_product_id_fkey;
ALTER TABLE fg_inventory   DROP CONSTRAINT IF EXISTS fg_inventory_product_id_fkey;

-- Step 2: Null out product_id on all transactional tables (will be re-resolved by rebuild script).
UPDATE invoices     SET product_id = NULL;
UPDATE sales_orders SET product_id = NULL;
UPDATE enquiries    SET product_id = NULL;
UPDATE fg_inventory SET product_id = NULL;

-- Step 3: Drop the old products table (RMS-sourced, 1,702 noisy rows).
DROP TABLE IF EXISTS product_rms_specs CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- Step 4: Create new products table — canonical catalog with SERIAL PK.
CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    product_type    VARCHAR(100) NOT NULL,           -- canonical: 'GI Wire', 'MS Wire', etc.
    size_mm         FLOAT,                           -- numeric size for sorting
    size_label      VARCHAR(100) NOT NULL,           -- '0.90 mm', '6F 7.0 mm', '6.1 x 1.40 mm'
    grade           VARCHAR(50),                     -- optional refinement
    unit_of_measure VARCHAR(10)  NOT NULL DEFAULT 'MT',
    display_name    VARCHAR(200) NOT NULL,
    hsn_code        VARCHAR(20),
    gst_pct         FLOAT        NOT NULL DEFAULT 18.0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    UNIQUE (product_type, size_label)
);

CREATE INDEX idx_products_type ON products(product_type);
CREATE INDEX idx_products_size ON products(size_mm);

-- Step 5: Create product_rms_specs (RMS variants as enrichment).
CREATE TABLE product_rms_specs (
    id                  SERIAL PRIMARY KEY,
    product_id          INTEGER REFERENCES products(id) ON DELETE CASCADE,
    erp_order_id        INTEGER,                     -- original ERP RMS order_id
    rms_order_no        VARCHAR(300) NOT NULL,       -- raw RMS spec text e.g. 'ROLLIFLEX 0.90 MM/COMMERCIAL'
    rms_product_type    VARCHAR(100),                -- raw RMS product_type
    is_active           BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_rms_product_id ON product_rms_specs(product_id);
CREATE INDEX idx_rms_erp_order  ON product_rms_specs(erp_order_id);

-- Step 6: Re-add FK constraints (now pointing at the new products table).
ALTER TABLE invoices
    ADD CONSTRAINT invoices_product_id_fkey
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;
ALTER TABLE sales_orders
    ADD CONSTRAINT sales_orders_product_id_fkey
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;
ALTER TABLE enquiries
    ADD CONSTRAINT enquiries_product_id_fkey
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;
ALTER TABLE fg_inventory
    ADD CONSTRAINT fg_inventory_product_id_fkey
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL;

-- Step 7: RLS policies (mirror existing tables).
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_products" ON products FOR SELECT USING (true);

ALTER TABLE product_rms_specs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_product_rms_specs" ON product_rms_specs FOR SELECT USING (true);

SELECT 'Migration 004 complete — canonical products schema ready.' AS status;
