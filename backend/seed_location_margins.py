import sys
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

INDIA_LOCATIONS = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool", "Tirupati", "Anantapur", "Kakinada", "Kadapa", "Rajahmundry"],
    "Arunachal Pradesh": ["Itanagar", "Naharlagun", "Pasighat"],
    "Assam": ["Guwahati", "Dibrugarh", "Silchar", "Jorhat", "Nagaon", "Tinsukia", "Tezpur"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia", "Darbhanga", "Arrah", "Begusarai", "Bihar Sharif"],
    "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba", "Rajnandgaon", "Raigarh"],
    "Delhi": ["New Delhi", "Delhi", "Dwarka", "Rohini", "Narela"],
    "Goa": ["Panaji", "Margao", "Vasco da Gama", "Mapusa"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Junagadh", "Gandhinagar", "Anand", "Nadiad", "Morbi", "Surendranagar", "Bharuch", "Vapi", "Navsari", "Valsad"],
    "Haryana": ["Faridabad", "Gurgaon", "Panipat", "Ambala", "Yamunanagar", "Rohtak", "Hisar", "Karnal", "Sonipat", "Panchkula"],
    "Himachal Pradesh": ["Shimla", "Dharamshala", "Solan", "Mandi", "Baddi"],
    "Jammu & Kashmir": ["Srinagar", "Jammu", "Anantnag", "Baramulla"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro Steel City", "Deoghar", "Hazaribagh"],
    "Karnataka": ["Bengaluru", "Hubli-Dharwad", "Mysore", "Kalaburagi", "Mangaluru", "Belagavi", "Davanagere", "Bellary", "Vijayapura", "Shimoga"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Kollam", "Thrissur", "Alappuzha", "Palakkad", "Kannur"],
    "Madhya Pradesh": ["Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain", "Sagar", "Dewas", "Satna", "Ratlam"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Thane", "Pimpri-Chinchwad", "Nashik", "Kalyan-Dombivli", "Vasai-Virar", "Aurangabad", "Navi Mumbai", "Solapur", "Mira-Bhayandar", "Bhiwandi", "Amravati", "Nanded", "Kolhapur", "Sangli", "Jalgaon", "Akola"],
    "Manipur": ["Imphal", "Thoubal"],
    "Meghalaya": ["Shillong", "Tura"],
    "Mizoram": ["Aizawl", "Lunglei"],
    "Nagaland": ["Kohima", "Dimapur", "Mokokchung"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Berhampur", "Sambalpur", "Puri", "Balasore"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali", "Pathankot", "Hoshiarpur"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Kota", "Bikaner", "Ajmer", "Udaipur", "Bhilwara", "Alwar", "Sikar"],
    "Sikkim": ["Gangtok", "Namchi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tiruppur", "Erode", "Vellore", "Thoothukudi", "Nagercoil"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam", "Ramagundam"],
    "Tripura": ["Agartala", "Dharmanagar"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Ghaziabad", "Agra", "Meerut", "Varanasi", "Prayagraj", "Bareilly", "Aligarh", "Moradabad", "Saharanpur", "Gorakhpur", "Noida", "Greater Noida", "Jhansi", "Muzaffarnagar", "Mathura"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur"],
    "West Bengal": ["Kolkata", "Howrah", "Darjeeling", "Siliguri", "Asansol", "Durgapur", "Bardhaman", "Malda", "Kharagpur"],
    "Andaman and Nicobar Islands": ["Port Blair"],
    "Chandigarh": ["Chandigarh"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Daman", "Silvassa", "Diu"],
    "Ladakh": ["Leh", "Kargil"],
    "Lakshadweep": ["Kavaratti"],
    "Puducherry": ["Pondicherry", "Karaikal"]
}

STATE_CODES = {
    "Andhra Pradesh": "AP", "Arunachal Pradesh": "AR", "Assam": "AS", "Bihar": "BR",
    "Chhattisgarh": "CG", "Delhi": "DL", "Goa": "GA", "Gujarat": "GJ",
    "Haryana": "HR", "Himachal Pradesh": "HP", "Jammu & Kashmir": "JK", "Jharkhand": "JH",
    "Karnataka": "KA", "Kerala": "KL", "Madhya Pradesh": "MP", "Maharashtra": "MH",
    "Manipur": "MN", "Meghalaya": "ML", "Mizoram": "MZ", "Nagaland": "NL",
    "Odisha": "OR", "Punjab": "PB", "Rajasthan": "RJ", "Sikkim": "SK",
    "Tamil Nadu": "TN", "Telangana": "TG", "Tripura": "TR", "Uttar Pradesh": "UP",
    "Uttarakhand": "UT", "West Bengal": "WB", "Andaman and Nicobar Islands": "AN",
    "Chandigarh": "CH", "Dadra and Nagar Haveli and Daman and Diu": "DN",
    "Ladakh": "LA", "Lakshadweep": "LD", "Puducherry": "PY"
}

STATE_CONFIGS = {
    "Chhattisgarh": {"margin": -4.0, "driver": "Primary steel manufacturing hub; cheapest raw material access.", "key_cities": "Raipur, Bhilai, Bilaspur"},
    "Jharkhand": {"margin": -4.0, "driver": "Tata Steel & SAIL presence; extremely dense MSME wire ecosystem.", "key_cities": "Jamshedpur, Bokaro, Ranchi"},
    "Odisha": {"margin": -3.5, "driver": "Massive primary steel capacity; low inbound freight for local units.", "key_cities": "Rourkela, Kalinganagar, Cuttack"},
    "West Bengal": {"margin": -3.0, "driver": "Historic engineering hub; intense local competition.", "key_cities": "Durgapur, Howrah, Asansol"},
    "Punjab": {"margin": -2.5, "driver": "Massive secondary steel and rolling mill hub; high market saturation.", "key_cities": "Mandi Gobindgarh, Ludhiana"},
    "Maharashtra": {"margin": 0.0, "driver": "High demand from auto/agriculture. Solid local secondary steel, but higher power costs than the East.", "key_cities": "Jalna, Pune, Solapur, Mumbai, Nagpur"},
    "Gujarat": {"margin": -1.0, "driver": "Massive engineering base; state MSME subsidies keep local competitor costs low.", "key_cities": "Rajkot, Ahmedabad, Surat, Vadodara"},
    "Rajasthan": {"margin": -1.0, "driver": "Proximity to Hindustan Zinc (Udaipur) helps galvanizers; decent secondary steel.", "key_cities": "Bhiwadi, Jaipur, Udaipur"},
    "Haryana": {"margin": -0.5, "driver": "Feeds the Delhi-NCR industrial and construction belt.", "key_cities": "Faridabad, Hisar, Panipat"},
    "Madhya Pradesh": {"margin": 0.0, "driver": "Central location balances freight; moderate local competition.", "key_cities": "Indore, Pithampur, Gwalior"},
    "Uttar Pradesh": {"margin": 0.5, "driver": "Massive market size; slightly higher logistics costs depending on the exact city.", "key_cities": "Kanpur, Ghaziabad, Noida"},
    "Andhra Pradesh": {"margin": 0.0, "driver": "Vizag Steel Plant presence anchors prices locally.", "key_cities": "Visakhapatnam (Vizag), Vijayawada"},
    "Karnataka": {"margin": 1.5, "driver": "JSW Bellary provides some local steel, but overall demand outpaces cheap supply.", "key_cities": "Bengaluru, Hubballi, Belagavi"},
    "Tamil Nadu": {"margin": 2.5, "driver": "Heavy automotive/textile demand; high inbound freight from steel hubs.", "key_cities": "Chennai, Coimbatore, Tiruppur"},
    "Kerala": {"margin": 4.0, "driver": "Very low local production; practically all wire products are imported from other states.", "key_cities": "Kochi, Palakkad, Thiruvananthapuram"},
    "Assam": {"margin": 5.0, "driver": "Difficult logistics terrain; high transit times allow for premium pricing.", "key_cities": "Guwahati, Silchar"},
    "Uttarakhand": {"margin": 3.0, "driver": "Mountainous terrain increases last-mile delivery costs, reducing competitive density.", "key_cities": "Pantnagar, Baddi"},
    "Bihar": {"margin": 2.0, "driver": "High construction demand but relatively few local wire-drawing MSMEs.", "key_cities": "Patna, Muzaffarpur"},
    "Telangana": {"margin": 0.0, "driver": "High industrial demand (infrastructure/solar); balanced by proximity to Vizag and Odisha steel.", "key_cities": "Hyderabad, Warangal"},
    "Goa": {"margin": 2.0, "driver": "Small market, high real estate/freight costs, no local wire rod production.", "key_cities": "Panaji, Madgaon"},
    "Himachal Pradesh": {"margin": 3.0, "driver": "Industrial hub in Baddi gets tax incentives, but mountainous terrain increases delivery costs.", "key_cities": "Baddi, Solan, Una"},
    "Arunachal Pradesh": {"margin": 5.0, "driver": "Deep North-East; extreme logistics friction.", "key_cities": "Itanagar"},
    "Manipur": {"margin": 5.0, "driver": "Deep North-East; high transit times and security/logistics overheads.", "key_cities": "Imphal"},
    "Meghalaya": {"margin": 4.0, "driver": "Byrnihat has some secondary steel units, but overall terrain commands a premium.", "key_cities": "Shillong, Byrnihat"},
    "Mizoram": {"margin": 5.0, "driver": "Deep North-East; purely a consumption market.", "key_cities": "Aizawl"},
    "Nagaland": {"margin": 5.0, "driver": "Deep North-East; high inbound logistics cost.", "key_cities": "Dimapur, Kohima"},
    "Sikkim": {"margin": 4.5, "driver": "High terrain, zero local metal production.", "key_cities": "Gangtok"},
    "Tripura": {"margin": 5.0, "driver": "Geographically isolated; heavily reliant on long-haul freight.", "key_cities": "Agartala"},
    "Delhi": {"margin": -0.5, "driver": "Hyper-competitive trading hub; highly connected to Haryana/UP mills.", "key_cities": "New Delhi"},
    "Dadra and Nagar Haveli and Daman and Diu": {"margin": -1.0, "driver": "Massive manufacturing/wire-drawing cluster due to historic tax benefits; highly competitive local pricing.", "key_cities": "Silvassa, Daman"},
    "Puducherry": {"margin": 2.0, "driver": "Pocketed within Tamil Nadu; high consumption but relies entirely on inbound freight.", "key_cities": "Puducherry"},
    "Jammu & Kashmir": {"margin": 4.0, "driver": "High security and terrain logistics friction; seasonal demand dips.", "key_cities": "Jammu, Srinagar"},
    "Ladakh": {"margin": 5.5, "driver": "Most extreme logistics terrain in India; very high freight baseline.", "key_cities": "Leh"},
    "Chandigarh": {"margin": -0.5, "driver": "Acts similarly to Punjab/Haryana border pricing.", "key_cities": "Chandigarh"},
    "Andaman and Nicobar Islands": {"margin": 7.0, "driver": "Requires sea freight; extreme premium zone.", "key_cities": "Port Blair"},
    "Lakshadweep": {"margin": 7.0, "driver": "Requires sea freight; highest logistical premium.", "key_cities": "Kavaratti"}
}

def main():
    print("Clearing existing entries in location_margin_config...")
    try:
        sb.table("location_margin_config").delete().neq("id", -9999).execute()
        print("Cleared successfully.")
    except Exception as e:
        print(f"Warning: could not clear: {e}")
        
    rows = []
    seen_region_ids = set()
    
    for state_name, cities in INDIA_LOCATIONS.items():
        state_code = STATE_CODES.get(state_name, state_name[:2].upper())
        state_cfg = STATE_CONFIGS.get(state_name, {"margin": 0.0, "driver": None, "key_cities": None})
        
        # is_competitive is based on margin_adjustment_pct being < 0, or mentions of 'competitive'
        is_comp = state_cfg["margin"] < 0 or (state_cfg["driver"] and "competiti" in state_cfg["driver"].lower())
        
        for city in cities:
            # Generate unique region_id
            clean_city = "".join(x for x in city if x.isalnum()).upper()
            region_id = f"{state_code}_{clean_city}"
            
            # Capping region_id at 20 chars just in case (schema limit VARCHAR(20))
            region_id = region_id[:20]
            
            # Ensure unique region_id
            if region_id in seen_region_ids:
                continue
            seen_region_ids.add(region_id)
            
            rows.append({
                "location_name": city,
                "region_id": region_id,
                "region_name": f"{city}, {state_name}",
                "state_code": state_code,
                "gst_type": "IGST" if state_code != "MH" else "CGST_SGST",
                "additional_tax_pct": 0.0,
                "freight_per_mt": 0.0,
                "is_competitive": bool(is_comp),
                "margin_adjustment_pct": state_cfg["margin"],
                "market_driver": state_cfg["driver"],
                "notes": f"System seeded location - {city} in {state_name}",
                "is_active": True
            })
            
    print(f"Prepared {len(rows)} location records. Loading in batches of 200...")
    total = 0
    for i in range(0, len(rows), 200):
        batch = rows[i:i+200]
        sb.table("location_margin_config").insert(batch).execute()
        total += len(batch)
        print(f"Loaded {total}/{len(rows)}")
        
    print("Location margin configuration successfully seeded!")

if __name__ == '__main__':
    main()
