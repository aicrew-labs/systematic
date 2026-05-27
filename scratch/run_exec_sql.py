import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

query = """
ALTER TABLE location_margin_config ADD COLUMN IF NOT EXISTS market_driver TEXT;
ALTER TABLE location_margin_config ADD COLUMN IF NOT EXISTS key_cities TEXT;
"""

print("Running migration query via exec_sql...")
response = requests.post(url, headers=headers, json={"query": query})
print("Status Code:", response.status_code)
print("Response Text:", response.text)
