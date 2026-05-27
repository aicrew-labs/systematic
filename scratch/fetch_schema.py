import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

url = f"{SUPABASE_URL}/rest/v1/"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

print("Fetching OpenAPI schema from PostgREST...")
response = requests.get(url, headers=headers)
print("Status:", response.status_code)

if response.status_code == 200:
    schema = response.json()
    paths = list(schema.get("paths", {}).keys())
    print("\nAvailable Endpoints:")
    for path in sorted(paths):
        print(f"  {path}")
else:
    print("Error:", response.text)
