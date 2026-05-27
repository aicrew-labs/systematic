import os
import random
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    print("Fetching locations from location_margin_config...")
    locations_res = sb.table("location_margin_config").select("region_id, location_name").limit(1000).execute()
    locations = locations_res.data
    
    if not locations:
        print("No locations found in location_margin_config. Exiting.")
        return

    location_map = {loc["location_name"].lower(): loc["region_id"] for loc in locations}
    all_region_ids = [loc["region_id"] for loc in locations]

    print("Fetching customers...")
    # Fetch all customers with pagination
    customers = []
    limit = 1000
    offset = 0
    while True:
        res = sb.table("customers").select("id, name, region_id").range(offset, offset + limit - 1).execute()
        customers.extend(res.data)
        if len(res.data) < limit:
            break
        offset += limit

    if not customers:
        print("No customers found. Exiting.")
        return

    print(f"Processing {len(customers)} customers...")
    
    updates = []
    for customer in customers:
        customer_name = customer.get("name", "").lower()
        assigned_region_id = None

        for city_name, region_id in location_map.items():
            if city_name in customer_name:
                assigned_region_id = region_id
                break
        
        if not assigned_region_id:
            assigned_region_id = random.choice(all_region_ids)
        
        if customer.get("region_id") != assigned_region_id:
            updates.append({"id": customer["id"], "region_id": assigned_region_id})

    print(f"Found {len(updates)} customers to update. Updating concurrently...")
    
    # Update concurrently
    def update_customer(update_data):
        try:
            sb.table("customers").update({"region_id": update_data["region_id"]}).eq("id", update_data["id"]).execute()
        except Exception as e:
            pass # ignore errors

    with ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(update_customer, updates))

    print(f"Successfully updated customers.")

if __name__ == '__main__':
    main()
