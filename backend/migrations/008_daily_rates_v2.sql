-- Migration 008: Rebuild daily_rates table
DROP TABLE IF EXISTS daily_rates CASCADE;

CREATE TABLE daily_rates (
    id                        SERIAL PRIMARY KEY,
    rate_date                 DATE NOT NULL DEFAULT CURRENT_DATE,
    prime_steel_rate          FLOAT NOT NULL,
    hc_steel_rate             FLOAT NOT NULL,
    commercial_steel_rate     FLOAT NOT NULL,
    zinc_sgh_rate             FLOAT NOT NULL,
    zinc_rate                 FLOAT NOT NULL,
    wire_rod_rate             FLOAT NOT NULL,
    conv_wiping_fine_rate     FLOAT NOT NULL,
    conv_wiping_thick_rate    FLOAT NOT NULL,
    conv_heavy_fine_rate      FLOAT NOT NULL,
    conv_heavy_thick_rate     FLOAT NOT NULL,
    conv_printing_rate        FLOAT NOT NULL,
    conv_stranding_rate       FLOAT NOT NULL,
    entered_by                VARCHAR(100),
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE daily_rates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_daily_rates" ON daily_rates FOR SELECT USING (true);
CREATE POLICY "public_insert_daily_rates" ON daily_rates FOR INSERT WITH CHECK (true);
