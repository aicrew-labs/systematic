import asyncio, aiohttp, json, re
from supabase import create_client

SUPABASE_URL = "https://bgccqhsfkxghcaetjngc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJnY2NxaHNma3hnaGNhZXRqbmdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMTY5OCwiZXhwIjoyMDk0Njc3Njk4fQ.8_6Gn7fYrSj0JQYg9LP87coNnf3IgGW2h8mybghEcS0"
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# Map base string to known types
def extract_type_and_size(prod_code):
    prod_code = str(prod_code).strip()
    known_types = [
        "ACSR Core Wire", "ACSR", "GI Wire", "MS Wire", "HC Patented Wire", "OFC Cable", 
        "GI Strip", "Zinc Dross", "PC Wire", "Barbed Wire", "Chain Link"
    ]
    for t in known_types:
        if prod_code.upper().startswith(t.upper()):
            size = prod_code[len(t):].strip()
            # clean leading hyphens or spaces
            size = re.sub(r'^[-:\s]+', '', size)
            return t, size
    
    # If no known type, guess the first 2 words
    parts = prod_code.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}", " ".join(parts[2:])
    return prod_code, ""

async def fetch_prods(session, order_id, order_no):
    try:
        async with session.post('https://systematic.ominfo.in/erp/web_crm.php', data={'action': 'getcyncustdata', 'order_id': order_id}) as resp:
            text = await resp.text()
            j = json.loads(text)
            prods = [p['prod_code'] for p in j.get('products', [])]
            return order_no, prods
    except:
        return order_no, []

async def main():
    print("Loading sales orders...")
    with open('c:/Personal/Projects/systematic/systematic/erp_data/sales_orders.json') as f:
        so_data = json.load(f)
    
    # First, let's login to get a cookie
    import requests
    s = requests.Session()
    s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})
    cookies = s.cookies.get_dict()

    print(f"Fetching products for {len(so_data)} orders...")
    connector = aiohttp.TCPConnector(limit=15)
    async with aiohttp.ClientSession(connector=connector, cookies=cookies) as session:
        tasks = []
        # Let's process all
        for so in so_data:
            tasks.append(fetch_prods(session, so['order_id'], so.get('order_no', '')))
        
        results = await asyncio.gather(*tasks)

    print("Updating Supabase...")
    updates_made = 0
    # Map order_no -> product info
    # We will update rows in quote_history where size_label == order_no
    # (Since we temporarily used order_no as size_label for SOs)
    
    # Pre-fetch all IDs to update locally, then batch update
    resp = sb.table("quote_history").select("id, size_label").eq("outcome", "won").execute()
    db_rows = resp.data
    order_to_id = {}
    for r in db_rows:
        order_to_id[r['size_label']] = r['id']
    
    for order_no, prods in results:
        if not prods: continue
        if order_no not in order_to_id: continue
        
        # We will use the FIRST product in the list as the primary for the quote history line item
        ptype, psize = extract_type_and_size(prods[0])
        if not psize: psize = "Standard"
        
        sb.table("quote_history").update({
            "product_type": ptype,
            "size_label": psize
        }).eq("id", order_to_id[order_no]).execute()
        updates_made += 1
        if updates_made % 100 == 0:
            print(f"  Updated {updates_made} records...")
            
    print(f"Done! Updated {updates_made} records in Supabase.")

asyncio.run(main())
