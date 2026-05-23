-- ============================================================
-- Migration 003: Widen text columns that overflowed VARCHAR(100)
-- Run in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- payment_terms: ERP rows can carry full freeform clauses up to ~220 chars.
ALTER TABLE invoices       ALTER COLUMN payment_terms TYPE VARCHAR(500);
ALTER TABLE sales_orders   ALTER COLUMN payment_terms TYPE VARCHAR(500);

-- dispatch_from: full address strings up to ~150 chars.
ALTER TABLE invoices       ALTER COLUMN dispatch_from TYPE VARCHAR(500);
ALTER TABLE sales_orders   ALTER COLUMN dispatch_from TYPE VARCHAR(500);

SELECT 'Migration 003 complete — columns widened.' AS status;
