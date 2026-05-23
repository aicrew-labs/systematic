"""Run a SQL migration via Supabase Management API.

Reads SBP_TOKEN from .env (or the environment).
"""
import json, sys, os, urllib.request

from dotenv import load_dotenv
load_dotenv()

PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF", "bgccqhsfkxghcaetjngc")
TOKEN = os.getenv("SBP_TOKEN")
if not TOKEN:
    raise SystemExit("ERROR: SBP_TOKEN must be set in .env (Supabase Management API token).")

if len(sys.argv) < 2:
    raise SystemExit("Usage: python3 run_migration.py path/to/migration.sql")

sql_path = sys.argv[1]
with open(sql_path) as f:
    sql = f.read()

req = urllib.request.Request(
    f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
    data=json.dumps({"query": sql}).encode(),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 quote-intel-migrator",
    },
    method="POST",
)
try:
    resp = urllib.request.urlopen(req)
    print("OK:", resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}:", e.read().decode())
    sys.exit(1)
