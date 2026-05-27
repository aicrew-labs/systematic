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
                "gst_type": "IGST" if state_code != "MH" else "CGST_SGST", # Sayli/Veritas are MH/GJ/etc. Inter-state defaults to IGST
                "additional_tax_pct": 0.0,
                "freight_per_mt": 0.0,
                "is_competitive": False,
                "margin_adjustment_pct": 0.0,
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
