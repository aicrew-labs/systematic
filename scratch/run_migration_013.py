import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("Missing SUPABASE credentials")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

with open(os.path.join(os.path.dirname(__file__), "..", "backend", "migrations", "013_add_feedback.sql"), "r") as f:
    sql = f.read()

# Execute SQL via RPC if exists, or print for manual execution
print(f"Please run the following SQL in Supabase SQL editor (or we can use RPC if exec_sql is available):\n\n{sql}")
