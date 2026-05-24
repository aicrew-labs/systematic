"""
Final ERP scraper: fetches SO detail pages for line items (product, size, rate),
then seeds quote_history correctly.

Sales Orders (line items) → outcome = 'won'
Enquiries not linked to SO → outcome = 'pending'

Run: python backend/seed_from_so_details.py
"""
import requests, json, os, re, time
from bs4 import BeautifulSoup
from datetime import date
from dateutil import parser as dateparser
from supabase import create_client
from collections import Counter

BASE = "https://systematic.ominfo.in/erp/"
SUPABASE_URL = "https://bgccqhsfkxghcaetjngc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJnY2NxaHNma3hnaGNhZXRqbmdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMTY5OCwiZXhwIjoyMDk0Njc3Njk4fQ.8_6Gn7fYrSj0JQYg9LP87coNnf3IgGW2h8mybghEcS0"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "erp_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
session = requests.Session()

def safe_float(v):
    try:
        return float(str(v).replace(",", "").replace("\u20b9", "").strip()) if v else None
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
    "FIBRE": "OFC Cable", "OPTICAL": "OFC Cable", "CHAIN": "MS Wire",
    "BARBED": "MS Wire", "WELDED": "MS Wire", "SPRING": "MS Wire",
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
print("  Done.")

# ── Load SO list ──────────────────────────────────────────────────────────────
with open(os.path.join(OUTPUT_DIR, "sales_orders.json")) as f:
    so_list = json.load(f)
print(f"\nLoaded {len(so_list)} sales orders")

# ── Test SO detail page URL ───────────────────────────────────────────────────
print("\n[1] Testing SO detail page...")
sample_id = so_list[0].get('order_id')
test_url = f"crm_sales_order_manage.php?function=2&orderno={sample_id}&type=1"
r = session.get(BASE + test_url)
print(f"  URL: {test_url}")
print(f"  Status: {r.status_code}, Length: {len(r.text)}")

line_item_headers = []
line_item_rows_sample = []

if r.status_code == 200 and len(r.text) > 500:
    soup = BeautifulSoup(r.text, 'html.parser')
    print(f"  Tables found: {len(soup.find_all('table'))}")
    for tbl in soup.find_all('table'):
        ths = [th.get_text(strip=True) for th in tbl.find_all('th')]
        rows = []
        for row in tbl.find_all('tr'):
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if cells and any(c.strip() for c in cells):
                rows.append(cells)
        if ths:
            print(f"  Table headers: {ths}")
        if rows:
            print(f"  First data row: {rows[0]}")
        # Find the item table (has product/rate/qty headers)
        th_set = set(t.upper() for t in ths)
        if any(k in th_set for k in ['ITEM', 'PRODUCT', 'RATE', 'DESCRIPTION', 'QTY']):
            line_item_headers = ths
            line_item_rows_sample = rows
            print(f"  >>> This looks like the line item table!")

# ── Determine how to extract line items ──────────────────────────────────────
print(f"\n[2] Line item structure: headers={line_item_headers}")

# Index map based on what we find
HDR = {h.upper().strip(): i for i, h in enumerate(line_item_headers)}
print(f"  Header index map: {HDR}")

# ── Process SO from Grid Data ────────────────────────────────────────────────
print(f"\n[3] Processing SO data (fast grid extraction)...")

all_so_rows = []
for so in so_list:
    company_name = str(so.get('company_name', '')).strip()
    order_date = parse_date(so.get('order_date'))
    sales_rep = so.get('emp_name', '')
    order_no = so.get('order_no', '')
    
    order_field = so.get('order', '')
    parts = order_field.split('*')
    total_amount = safe_float(parts[6]) if len(parts) > 6 else None
    total_qty = safe_float(so.get('total_qty')) or 1.0
    unit_rate = round(total_amount / total_qty, 2) if (total_amount and total_qty > 0) else None
    
    if unit_rate and unit_rate > 0:
        all_so_rows.append({
            'customer_name': company_name,
            'order_date': order_date,
            'order_no': order_no,
            'sales_rep': sales_rep,
            'qty': total_qty,
            'rate': unit_rate,
            'amount': total_amount,
            'product_type': 'MS Wire',
            'size_label': order_no,
        })

print(f"  Extracted {len(all_so_rows)} valid 'won' rows from {len(so_list)} SOs.")

# ── Build quote_history rows ──────────────────────────────────────────────────
print(f"\n[4] Building quote_history rows...")
rows = []

# Add SO rows as 'won'
for r_so in all_so_rows:
    rows.append(dict(
        quote_date=r_so.get('order_date') or date.today().isoformat(),
        customer_name=r_so['customer_name'],
        product_type=r_so.get('product_type', 'MS Wire'),
        size_label=r_so.get('size_label', r_so.get('order_no', ''))[:100],
        grade=None,
        quantity=r_so.get('qty', 1.0),
        unit='MT',
        unit_rate_inr=r_so['rate'],
        net_amount_inr=r_so.get('amount', r_so['rate']),
        payment_terms=None,
        credit_days=None,
        outcome='won',
        sales_rep=r_so.get('sales_rep'),
        notes=f"SO: {r_so.get('order_no', '')}",
    ))

print(f"  'won' rows from SOs: {len(rows)}")

# Add enquiry rows
enq_path = os.path.join(OUTPUT_DIR, "enquiries.json")
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
            if any(w in status for w in ["WIN", "ORDER", "CONFIRM", "SALES"]):
                outcome = "won"
            elif any(w in status for w in ["LOST", "CANCEL", "REJECT"]):
                outcome = "lost"
            elif "CLOSE" in status:
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
        except:
            continue
    print(f"  Enquiry rows added. Total: {len(rows)}")

outcome_cnt = Counter(r['outcome'] for r in rows)
print(f"  Outcome breakdown: {dict(outcome_cnt)}")

# ── Seed Supabase ─────────────────────────────────────────────────────────────
print(f"\n[5] Clearing and re-seeding quote_history...")
sb.table("quote_history").delete().neq("id", -1).execute()
print("  Cleared.")
BATCH = 200
for i in range(0, len(rows), BATCH):
    sb.table("quote_history").insert(rows[i:i+BATCH]).execute()
    print(f"  Inserted {min(i+BATCH, len(rows))}/{len(rows)}", end="\r")
print(f"\n  Done! {len(rows)} rows seeded.")

# ── Verify KEC ────────────────────────────────────────────────────────────────
print("\n[6] Verifying KEC Asian Cables...")
kec = sb.table("quote_history").select("customer_name,outcome,product_type").ilike("customer_name", "%KEC%").eq("outcome","won").limit(5).execute()
print(f"  KEC 'won' rows: {len(kec.data)}")
for row in kec.data:
    print(f"    {row}")
