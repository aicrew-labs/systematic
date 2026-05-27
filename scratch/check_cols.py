import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

try:
    res = sb.table("location_margin_config").select("market_driver, key_cities").limit(1).execute()
    print("Success! Columns exist!")
except Exception as e:
    print("Columns do not exist. Error:", e)
