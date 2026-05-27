import os
import sys
import time
import math
import requests
from dotenv import load_dotenv
from supabase import create_client

# Daman coordinates
DAMAN_LAT = 20.3974
DAMAN_LON = 72.8328

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_coordinates(city, state):
    query = f"{city}, {state}, India"
    url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&limit=1"
    headers = {'User-Agent': 'SystematicQuoteApp/1.0'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Error fetching {query}: {e}")
    
    return None, None

def main():
    # Setup Supabase client
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Missing Supabase credentials")
        sys.exit(1)
        
    supabase = create_client(url, key)
    
    print("Fetching locations...")
    response = supabase.table('location_margin_config').select('id, location_name, region_name').execute()
    locations = response.data
    
    print(f"Found {len(locations)} locations to update.")
    
    for loc in locations:
        loc_id = loc['id']
        city = loc['location_name']
        state = loc['region_name'].split(", ")[-1] if ", " in loc['region_name'] else ""
        
        # Don't rate limit too hard, sleep 1 second
        time.sleep(1)
        
        lat, lon = get_coordinates(city, state)
        if lat and lon:
            straight_line_dist = haversine(DAMAN_LAT, DAMAN_LON, lat, lon)
            # Route factor approx 1.3 for Indian roads
            road_dist = int(straight_line_dist * 1.3)
            print(f"[{city}, {state}] -> {road_dist} km (Straight: {straight_line_dist:.1f})")
            
            # Update DB
            supabase.table('location_margin_config').update({"distance_km": road_dist}).eq("id", loc_id).execute()
        else:
            print(f"[{city}, {state}] -> Coordinates not found. Skipping.")

if __name__ == "__main__":
    main()
