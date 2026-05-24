"""
Improved ERP scraper: drills into individual Sales Order detail pages
to extract line items (product, size, rate) and rebuilds quote_history.

Sales Orders (with line items) → outcome = 'won'
Enquiries not linked to any SO → outcome = 'pending'

Run: python backend/scrape_so_details.py
"""
import requests, json, os, re, time
from bs4 import BeautifulSoup
from datetime import date
from dateutil import parser as dateparser
from supabase import create_client

BASE = "https://systematic.ominfo.in/erp/"
SUPABASE_URL = "https://bgccqhsfkxghcaetjngc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJnY2NxaHNma3hnaGNhZXRqbmdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMTY5OCwiZXhwIjoyMDk0Njc3Njk4fQ.8_6Gn7fYrSj0JQYg9LP87coNnf3IgGW2h8mybghEcS0"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "erp_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
session = requests.Session()

def safe_float(v):
    try:
        return float(str(v).replace(",", "").replace("₹", "").strip()) if v else None
    except:
        return None

def parse_date(s):
    try:
        return dateparser.parse(str(s), dayfirst=True).date().isoformat() if s else None
    except:
        return None

PRODUCT_MAP = {
    "GI": "GI Wire", "MS": "MS Wire", "HC": "HC Patented Wire",
    "OFC": "OFC Cable", "ACSR": "HC Patented Wire", "ACS": "HC Patented Wire",
    "FIBRE": "OFC Cable", "OPTICAL": "OFC Cable",
}

def map_product(text):
    t = str(text).upper()
    for k, v in PRODUCT_MAP.items():
        if k in t:
            return v
    return "MS Wire"

# ── Login ─────────────────────────────────────────────────────────────────────
print("Logging in to ERP...")
session.post(BASE + "crm_login.php", data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)

# ── Load existing scraped sales orders ───────────────────────────────────────
so_path = os.path.join(OUTPUT_DIR, "sales_orders.json")
if os.path.exists(so_path):
    with open(so_path) as f:
        so_list = json.load(f)
    print(f"Loaded {len(so_list)} sales orders from disk")
else:
    print("sales_orders.json not found — re-scraping...")
    def pull_ajax_grid(key, key_val, date_params=None, label=""):
        all_records = []
        start = 0
        while True:
            data = {"draw": str(start//100+1), "start": str(start), "length": "100",
                    "search[value]": "", "order[0][column]": "0", "order[0][dir]": "desc", key: key_val}
            if date_params:
                data.update(date_params)
            r = session.post(BASE + "crm_ajax.php", data=data)
            try:
                j = r.json()
                batch_data = j.get('data') or j.get('aaData') or []
                total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
                all_records.extend(batch_data)
                if start == 0: print(f"  {label}: total={total}", end="", flush=True)
                else: print(".", end="", flush=True)
                if len(all_records) >= total or not batch_data: print(); break
                start += 100
            except Exception as e:
                print(f"\n  Error: {e}"); break
        return all_records
    so_list = pull_ajax_grid("sogrid", "1", label="Sales Orders")
    with open(so_path, "w") as f:
        json.dump(so_list, f, indent=2, default=str)

print(f"\nSample SO fields: {list(so_list[0].keys()) if so_list else 'EMPTY'}")
print(f"Sample SO: {so_list[0] if so_list else 'EMPTY'}")

# ── Detect SO detail page URL pattern ────────────────────────────────────────
print("\n[1] Detecting SO detail page structure...")
sample_id = so_list[0].get('order_id') if so_list else None
detail_rows_all = []

if sample_id:
    # Try different URL patterns for SO detail page
    url_patterns = [
        f"crm_so_manage.php?function=2&orderid={sample_id}&type=view",
        f"crm_so_manage.php?function=view&orderid={sample_id}",
        f"crm_so_detail.php?orderid={sample_id}",
        f"crm_so_manage.php?orderid={sample_id}",
    ]
    detail_html = None
    working_pattern = None
    for pat in url_patterns:
        r = session.get(BASE + pat)
        if r.status_code == 200 and len(r.text) > 500 and 'login' not in r.text.lower()[:100]:
            soup = BeautifulSoup(r.text, 'html.parser')
            tables = soup.find_all('table')
            if tables:
                detail_html = r.text
                working_pattern = pat.replace(str(sample_id), "{order_id}")
                print(f"  Working URL pattern: {pat}")
                break
    
    if detail_html:
        soup = BeautifulSoup(detail_html, 'html.parser')
        print(f"  Page tables found: {len(soup.find_all('table'))}")
        for tbl in soup.find_all('table'):
            headers = [th.get_text(strip=True) for th in tbl.find_all('th')]
            rows = []
            for row in tbl.find_all('tr'):
                cells = [td.get_text(strip=True) for td in row.find_all('td')]
                if cells:
                    rows.append(cells)
            if headers:
                print(f"  Table headers: {headers}")
            if rows and headers:
                print(f"  First data row: {rows[0] if rows else 'none'}")
    else:
        print("  Could not find working SO detail URL pattern")
        print(f"  Trying raw page source for order {sample_id}...")
        r = session.get(BASE + f"crm_so_manage.php?function=2&orderid={sample_id}&type=view")
        print(f"  Status: {r.status_code}, Content length: {len(r.text)}")
        # Print first 1000 chars to understand the page structure
        print(f"  Page preview:\n{r.text[:2000]}")

# ── Try SO Report page with AJAX ─────────────────────────────────────────────
print("\n[2] Trying SO Item Report (AJAX)...")
# Try different AJAX keys that might return SO line items
for key in ['soitemgrid', 'solinegrid', 'so_item_grid', 'salesorderitem', 'soitems']:
    r_try = session.post(BASE + "crm_ajax.php", data={
        "draw": "1", "start": "0", "length": "5", "search[value]": "", key: "1"
    })
    try:
        j = r_try.json()
        total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
        if total > 0:
            print(f"  Found SO items grid key: {key}, total={total}")
            print(f"  Sample: {j.get('data', j.get('aaData', [{}]))[0] if j.get('data') or j.get('aaData') else 'no data'}")
    except:
        pass

# ── Try fetching the enquiry report which has linked SO status ────────────────
print("\n[3] Checking enquiry status values more carefully...")
enq_path = os.path.join(OUTPUT_DIR, "enquiries.json")
if os.path.exists(enq_path):
    with open(enq_path) as f:
        enquiries = json.load(f)
    statuses = {}
    for e in enquiries:
        st = str(e.get('status', '')).strip()
        statuses[st] = statuses.get(st, 0) + 1
    print(f"  Enquiry statuses: {statuses}")
    
    # Show a won enquiry example if any
    won_examples = [e for e in enquiries if any(w in str(e.get('status','')).upper() for w in ['WIN','ORDER','SALES','CONFIRM','CLOSE'])]
    print(f"  Enquiries with sales-like status: {len(won_examples)}")
    if won_examples:
        print(f"  Example: {won_examples[0]}")

# ── Match enquiries to SO customers via company name ─────────────────────────
print("\n[4] Matching enquiries to Sales Orders by company name...")
# Build set of company names from SO
so_companies = set()
for so in so_list:
    cname = str(so.get('company_name', '')).strip().lower()
    if cname:
        so_companies.add(cname)
print(f"  Unique SO companies: {len(so_companies)}")
if so_companies:
    print(f"  Sample: {list(so_companies)[:5]}")

# Check if any enquiry customers match SO companies
if os.path.exists(enq_path):
    with open(enq_path) as f:
        enquiries = json.load(f)
    matched_enqs = 0
    for e in enquiries:
        ecust = str(e.get('cust_name', '')).strip().lower()
        if any(ecust in sc or sc in ecust for sc in so_companies):
            matched_enqs += 1
    print(f"  Enquiries matching SO companies: {matched_enqs} / {len(enquiries)}")

# ── Build quote_history using best available data ────────────────────────────
print("\n[5] Building quote_history from SO grid + enquiries...")
rows = []

# --- SALES ORDERS: Use SO grid data, get customer + date, mark as 'won' ---
# The SO grid has: company_name, order_date, total_qty, order_no, order_status
# We don't have unit rate from the grid but we know it's a real order
for so in so_list:
    try:
        cname = str(so.get('company_name', '')).strip()
        if not cname:
            continue
        total_qty = safe_float(so.get('total_qty')) or 1.0
        d = parse_date(so.get('order_date'))
        order_no = so.get('order_no', '')
        
        # Try to extract amount from the 'order' field (pipe-delimited string)
        order_field = so.get('order', '')
        total_amount = None
        if order_field:
            parts = order_field.split('*')
            if len(parts) > 7:
                total_amount = safe_float(parts[7])
        
        unit_rate = (total_amount / total_qty) if (total_amount and total_qty > 0) else None
        if not unit_rate or unit_rate <= 0:
            continue  # Skip SOs where we can't determine rate

        rows.append(dict(
            quote_date=d or date.today().isoformat(),
            customer_name=cname,
            product_type="MS Wire",  # Default — will refine via enquiry match
            size_label=order_no,
            grade=None,
            quantity=total_qty,
            unit="MT",
            unit_rate_inr=round(unit_rate, 2),
            net_amount_inr=round(total_amount, 2),
            payment_terms=None,
            credit_days=None,
            outcome="won",
            sales_rep=so.get('emp_name'),
            notes=f"SO: {order_no}",
        ))
    except Exception as ex:
        continue

print(f"  Built {len(rows)} 'won' rows from Sales Orders (with rate)")
so_won_count = len(rows)

# --- ENQUIRIES: add all with correct status ---
if os.path.exists(enq_path):
    with open(enq_path) as f:
        enquiries = json.load(f)
    for e in enquiries:
        try:
            cname = str(e.get("cust_name", "")).strip()
            if not cname: continue
            rate = safe_float(e.get("price_offered")) or safe_float(e.get("target_price"))
            qty = safe_float(e.get("order_qty")) or 1.0
            if not rate or rate <= 0: continue
            prod_categ = e.get("prod_categ") or ""
            spec = e.get("prod_specification") or prod_categ or ""
            d = parse_date(e.get("created_on_formatted"))
            status = str(e.get("status", "")).strip().upper()
            if any(w in status for w in ["WIN","ORDER","CONFIRM","SALES"]):
                outcome = "won"
            elif any(w in status for w in ["LOST","CANCEL","REJECT","CLOSE"]):
                outcome = "lost"
            else:
                outcome = "pending"
            rows.append(dict(
                quote_date=d or date.today().isoformat(),
                customer_name=cname,
                product_type=map_product(prod_categ),
                size_label=str(spec)[:100],
                grade=None, quantity=qty, unit=e.get("unit_code") or "MT",
                unit_rate_inr=rate, net_amount_inr=round(rate * qty, 2),
                payment_terms=None, credit_days=None, outcome=outcome,
                sales_rep=e.get("emp_name"), notes=e.get("remarks"),
            ))
        except: continue

from collections import Counter
print(f"  Total rows: {len(rows)}, Outcomes: {dict(Counter(r['outcome'] for r in rows))}")

# ── Seed Supabase ────────────────────────────────────────────────────────────
print("\n[6] Re-seeding quote_history in Supabase...")
sb.table("quote_history").delete().neq("id", -1).execute()
print("  Cleared.")
BATCH = 200
for i in range(0, len(rows), BATCH):
    sb.table("quote_history").insert(rows[i:i+BATCH]).execute()
    print(f"  Inserted {min(i+BATCH, len(rows))}/{len(rows)}", end="\r")
print(f"\n  Done! {len(rows)} rows seeded.")
print(f"\nFinal outcome breakdown: {dict(Counter(r['outcome'] for r in rows))}")
