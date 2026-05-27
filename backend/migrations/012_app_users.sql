-- ============================================================
-- Run this SQL in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/bgccqhsfkxghcaetjngc/editor
-- ============================================================

-- Step 1: Create app_users table
CREATE TABLE IF NOT EXISTS app_users (
    id          SERIAL PRIMARY KEY,
    user_id     TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    full_name   TEXT NOT NULL,
    email       TEXT,
    role        TEXT DEFAULT 'user',
    is_active   BOOLEAN DEFAULT TRUE,
    last_login  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_users_user_id ON app_users(user_id);

-- Step 2: Insert default admin user (password: admin123)
INSERT INTO app_users (user_id, password, full_name, email, role, is_active)
VALUES (
    'admin',
    '$2b$12$Tat/qDaIOcFZB1T./Eaeee4i0vQdN9djCzAKQtkT1m/46V6e18i76',
    'Admin User',
    'admin@systematicltd.com',
    'admin',
    true
)
ON CONFLICT (user_id) DO NOTHING;
