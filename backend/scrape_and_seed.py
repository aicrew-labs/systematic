"""
Scrape Sales Orders and Enquiries from ERP, then re-seed quote_history
with correct outcome: sales orders = 'won', enquiries only = 'pending'.

Run: python backend/scrape_and_seed.py
"""
import requests, json, os, re
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

# ── Login ─────────────────────────────────────────────────────────────────────
print("Logging in to ERP...")
r = session.post(BASE + "crm_login.php", data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)
print(f"  Login status: {r.status_code}")

# ── AJAX grid puller ──────────────────────────────────────────────────────────
def pull_ajax_grid(key, key_val, date_params=None, label=""):
    all_records = []
    start = 0
    batch = 100
    while True:
        data = {
            "draw": str(start//batch + 1), "start": str(start), "length": str(batch),
            "search[value]": "", "order[0][column]": "0", "order[0][dir]": "desc", key: key_val
        }
        if date_params:
            data.update(date_params)
        r = session.post(BASE + "crm_ajax.php", data=data)
        try:
            j = r.json()
            batch_data = j.get('data') or j.get('aaData') or []
            total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
            all_records.extend(batch_data)
            if start == 0:
                print(f"  {label}: total={total}", end="", flush=True)
            else:
                print(".", end="", flush=True)
            if len(all_records) >= total or not batch_data:
                print()
                break
            start += batch
        except Exception as e:
            print(f"\n  Error pulling {label}: {e}")
            break
    return all_records

# ── STEP 1: Scrape Enquiries ──────────────────────────────────────────────────
print("\n[1] Scraping Enquiries...")
enquiries = pull_ajax_grid(
    key="enquiryreport", key_val="1",
    date_params={"min": "01-01-2020", "max": "31-12-2026", "rmname": "0"},
    label="Enquiries"
)
with open(os.path.join(OUTPUT_DIR, "enquiries.json"), "w") as f:
    json.dump(enquiries, f, indent=2, default=str)
print(f"  Saved {len(enquiries)} enquiries")

# ── STEP 2: Scrape Sales Orders ──────────────────────────────────────────────
print("\n[2] Scraping Sales Orders...")
so_data = []

# Try to detect SO grid key from the page
r_so = session.get(BASE + "crm_sales_order_grid.php")
so_key = None
for script in BeautifulSoup(r_so.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        m = re.search(r'data\.(\w+)\s*=\s*["\']1["\']', script.string)
        if m and m.group(1) not in ['clientAllData']:
            so_key = m.group(1)
            print(f"  Detected SO key: {so_key}")
            break

# Fallback: try common keys
if not so_key:
    for key in ['salesordergrid', 'sogrid', 'so_grid', 'salesorder', 'salesOrderGrid']:
        r_try = session.post(BASE + "crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
        try:
            j = r_try.json()
            total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
            if total > 0:
                print(f"  Found SO key: {key}, total={total}")
                so_key = key
                break
        except:
            pass

if so_key:
    so_data = pull_ajax_grid(
        key=so_key, key_val="1",
        date_params={"min": "01-01-2020", "max": "31-12-2026"},
        label="Sales Orders"
    )
    with open(os.path.join(OUTPUT_DIR, "sales_orders.json"), "w") as f:
        json.dump(so_data, f, indent=2, default=str)
    print(f"  Saved {len(so_data)} sales orders")
else:
    print("  WARNING: Could not detect Sales Order grid key. Checking raw page...")
    print("  Page keys found:", [s.string[:200] for s in BeautifulSoup(r_so.text, 'html.parser').find_all('script') if s.string and 'ajax' in s.string.lower()][:2])

# ── STEP 3: Build SO customer names set ─────────────────────────────────────
print("\n[3] Analysing data...")

# Collect all customer+product combos from sales orders
so_keys_set = set()
for so in so_data:
    # Common column names for SO data from ERP grids
    cname = (so.get("cust_name") or so.get("customer_name") or "").strip()
    if cname:
        so_keys_set.add(cname.lower())

print(f"  Unique SO customers: {len(so_keys_set)}")
if so_keys_set:
    examples = list(so_keys_set)[:5]
    print(f"  Sample SO customers: {examples}")

# Show sample enquiry record to understand field names
if enquiries:
    print(f"\n  Sample enquiry fields: {list(enquiries[0].keys())}")
    print(f"  Sample enquiry status: {enquiries[0].get('status','N/A')}")
    # Check unique status values
    statuses = set(str(e.get('status','')).strip() for e in enquiries)
    print(f"  Unique enquiry statuses: {sorted(statuses)}")

if so_data:
    print(f"\n  Sample SO fields: {list(so_data[0].keys())}")
    print(f"  Sample SO row: {so_data[0]}")

# ── STEP 4: Rebuild quote_history with correct outcomes ──────────────────────
print("\n[4] Rebuilding quote_history with correct outcomes...")

PRODUCT_MAP = {
    "GI": "GI Wire", "MS": "MS Wire", "HC": "HC Patented Wire",
    "OFC": "OFC Cable", "ACSR": "HC Patented Wire", "ACS": "HC Patented Wire",
}

def safe_float(v):
    try:
        return float(str(v).replace(",", "").strip()) if v else None
    except:
        return None

def parse_date(s):
    try:
        return dateparser.parse(str(s), dayfirst=True).date().isoformat() if s else None
    except:
        return None

def map_product(categ_str):
    c = str(categ_str).upper()
    for k, v in PRODUCT_MAP.items():
        if k in c:
            return v
    return "MS Wire"

rows = []

# --- Process Sales Orders as 'won' ---
for so in so_data:
    try:
        cname = (so.get("cust_name") or so.get("customer_name") or "").strip()
        if not cname:
            continue
        rate = safe_float(so.get("rate") or so.get("unit_rate") or so.get("price") or so.get("price_offered"))
        qty = safe_float(so.get("qty") or so.get("order_qty") or so.get("quantity")) or 1.0
        if not rate or rate <= 0:
            continue
        prod_categ = so.get("prod_categ") or so.get("product_type") or ""
        spec = so.get("prod_specification") or so.get("prod_spec") or so.get("item") or prod_categ or ""
        d = parse_date(so.get("created_on_formatted") or so.get("so_date") or so.get("order_date") or so.get("date"))
        rows.append(dict(
            quote_date=d or date.today().isoformat(),
            customer_name=cname,
            product_type=map_product(prod_categ),
            size_label=str(spec)[:100],
            grade=None,
            quantity=qty,
            unit=so.get("unit_code") or "MT",
            unit_rate_inr=rate,
            net_amount_inr=round(rate * qty, 2),
            payment_terms=so.get("payment_terms"),
            credit_days=None,
            outcome="won",  # Sales Order = Won
            sales_rep=so.get("emp_name") or so.get("sales_rep"),
            notes=so.get("remarks"),
        ))
    except Exception as ex:
        continue

print(f"  Built {len(rows)} 'won' rows from Sales Orders")
so_won_count = len(rows)

# --- Process Enquiries as 'pending' (if not already a sales order) ---
for e in enquiries:
    try:
        cname = str(e.get("cust_name", "")).strip()
        if not cname:
            continue
        rate = safe_float(e.get("price_offered")) or safe_float(e.get("target_price"))
        qty = safe_float(e.get("order_qty")) or 1.0
        if not rate or rate <= 0:
            continue
        prod_categ = e.get("prod_categ") or ""
        spec = e.get("prod_specification") or prod_categ or ""
        d = parse_date(e.get("created_on_formatted"))

        # Determine outcome from ERP status field
        status = str(e.get("status", "")).strip().upper()
        if "WIN" in status or "ORDER" in status or "CONFIRM" in status or "SALES ORDER" in status:
            outcome = "won"
        elif "LOST" in status or "CANCEL" in status or "REJECT" in status:
            outcome = "lost"
        else:
            outcome = "pending"

        rows.append(dict(
            quote_date=d or date.today().isoformat(),
            customer_name=cname,
            product_type=map_product(prod_categ),
            size_label=str(spec)[:100],
            grade=None,
            quantity=qty,
            unit=e.get("unit_code") or "MT",
            unit_rate_inr=rate,
            net_amount_inr=round(rate * qty, 2),
            payment_terms=None,
            credit_days=None,
            outcome=outcome,
            sales_rep=e.get("emp_name"),
            notes=e.get("remarks"),
        ))
    except Exception as ex:
        continue

print(f"  Total rows to insert: {len(rows)} ({so_won_count} won from SO + {len(rows)-so_won_count} from enquiries)")

# ── STEP 5: Clear and re-seed quote_history ──────────────────────────────────
print("\n[5] Re-seeding quote_history in Supabase...")
sb.table("quote_history").delete().neq("id", -1).execute()
print("  Cleared quote_history")

BATCH = 200
for i in range(0, len(rows), BATCH):
    batch = rows[i:i+BATCH]
    sb.table("quote_history").insert(batch).execute()
    print(f"  Inserted {min(i+BATCH, len(rows))}/{len(rows)} rows", end="\r")
print(f"\n  Done! {len(rows)} rows inserted.")

# ── SUMMARY ──────────────────────────────────────────────────────────────────
from collections import Counter
outcomes = Counter(r["outcome"] for r in rows)
print(f"\nOutcome breakdown: {dict(outcomes)}")
print("\nDone! quote_history rebuilt with real ERP data.")
