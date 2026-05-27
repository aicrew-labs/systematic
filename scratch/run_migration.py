"""
Run the app_users migration by executing SQL via Supabase admin REST endpoint.
Tries the service-role key route.
"""
import os, sys
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
PROJECT_REF = SUPABASE_URL.split("//")[1].split(".")[0] if SUPABASE_URL else "bgccqhsfkxghcaetjngc"

SQL = """
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
"""

# Try using the pg-proxy endpoint (available with service-role key in some setups)
# Supabase's REST API doesn't allow raw SQL, but we can try the pg endpoint
# Actually, let's use the direct postgres connection info if available
print("Attempting to run migration via Supabase Management API (v1/projects/{ref}/query)...")

# Try with a fresh approach: Supabase Management API needs a personal access token
# Let's try using psycopg2 with Supabase postgres connection string
try:
    import psycopg2
    
    # Supabase postgres connection string format:
    # postgresql://postgres.{ref}:{password}@aws-0-{region}.pooler.supabase.com:6543/postgres
    DB_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if DB_URL:
        print(f"Connecting via DATABASE_URL...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(SQL)
        conn.commit()
        cur.close()
        conn.close()
        print("Migration successful via DATABASE_URL!")
        sys.exit(0)
    else:
        print("DATABASE_URL not set, cannot use psycopg2 direct connection.")
except ImportError:
    print("psycopg2 not installed")
except Exception as e:
    print(f"psycopg2 error: {e}")

print("\n=== MANUAL ACTION REQUIRED ===")
print("Please run the following SQL in your Supabase dashboard:")
print("https://supabase.com/dashboard/project/bgccqhsfkxghcaetjngc/editor")
print()
print(SQL)
