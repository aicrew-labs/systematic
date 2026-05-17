"""
Systematic ERP — Full Data Scraper
Pulls all available data from every module and saves to JSON files.
"""
import requests, json, re, os
from bs4 import BeautifulSoup

BASE = "https://systematic.ominfo.in/erp/"
OUTPUT_DIR = "erp_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.post(BASE + "crm_login.php",
             data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)

def save(name, data):
    path = f"{OUTPUT_DIR}/{name}.json"
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  ✓ Saved {len(data) if isinstance(data, list) else 1} records → {path}")
    return data

def pull_ajax_grid(key, key_val, date_params=None, label=""):
    """Pull all pages from a DataTables AJAX endpoint."""
    all_records = []
    start = 0
    batch = 100
    while True:
        data = {
            "draw": str(start//batch + 1),
            "start": str(start),
            "length": str(batch),
            "search[value]": "",
            "order[0][column]": "0",
            "order[0][dir]": "desc",
            key: key_val
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
                print(f".", end="", flush=True)
            if len(all_records) >= total or not batch_data:
                print()
                break
            start += batch
        except Exception as e:
            print(f"\n  Error: {e} | Raw: {r.text[:100]}")
            break
    return all_records

def scrape_table_page(url, post_data=None):
    """Scrape an HTML table page, return headers and rows."""
    r = session.post(url, data=post_data) if post_data else session.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    results = []
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if not headers:
            continue
        rows = []
        for row in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if cells and any(c and c not in ['--', ''] for c in cells):
                rows.append(dict(zip(headers, cells)) if len(cells) == len(headers) else cells)
        if rows:
            results.append({"headers": headers, "rows": rows})
    return results

print("=" * 70)
print("SYSTEMATIC ERP — FULL DATA SCRAPE")
print("=" * 70)

# ─────────────────────────────────────────
# MODULE 1: CUSTOMERS
# ─────────────────────────────────────────
print("\n[1] CUSTOMERS")
customers = {}
for char in 'abcdefghijklmnopqrstuvwxyz0123456789':
    r = session.get(BASE + f"web_crm.php?searchData={char}")
    soup = BeautifulSoup(r.text, 'html.parser')
    for span in soup.find_all('span', class_='result1'):
        m = re.search(r"getCustomerDetails\((\d+),'([^']+)','([^']+)','([^']+)'\)", span.get('onclick',''))
        if m:
            cid, name, phone, cmpid = m.groups()
            customers[cid] = {"customer_id": cid, "name": name, "phone": phone, "company_id": cmpid}
print(f"  Total unique customers: {len(customers)}")
save("customers", list(customers.values()))

# ─────────────────────────────────────────
# MODULE 2: ENQUIRY REPORT (1,145 records confirmed)
# ─────────────────────────────────────────
print("\n[2] ENQUIRY REPORT")
enquiries = pull_ajax_grid(
    key="enquiryreport", key_val="1",
    date_params={"min": "01-01-2020", "max": "31-12-2026", "rmname": "0"},
    label="Enquiries"
)
save("enquiries", enquiries)

# ─────────────────────────────────────────
# MODULE 3: SALES ORDER GRID
# ─────────────────────────────────────────
print("\n[3] SALES ORDERS")
# Find the SO grid key from JS
r_so = session.get(BASE + "crm_sales_order_grid.php")
so_key = None
for script in BeautifulSoup(r_so.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        m = re.search(r'data\.(\w+)\s*=\s*["\']1["\']', script.string)
        if m and m.group(1) not in ['clientAllData']:
            so_key = m.group(1)
            break
print(f"  SO grid key: {so_key}")
if so_key:
    so_data = pull_ajax_grid(key=so_key, key_val="1", label="Sales Orders")
else:
    # Try common keys
    for key in ['salesordergrid', 'sogrid', 'so_grid', 'salesorder']:
        r_try = session.post(BASE + "crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
        try:
            j = r_try.json()
            total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
            if total > 0:
                print(f"  Found SO grid with key: {key}, total={total}")
                so_key = key
                break
        except: pass
    so_data = pull_ajax_grid(key=so_key, key_val="1", label="Sales Orders") if so_key else []
save("sales_orders", so_data)

# Try SO Report page (HTML table based)
print("  Trying SO Report page...")
so_report = scrape_table_page(BASE + "crm_so_report.php")
if so_report:
    save("so_report", so_report)

# ─────────────────────────────────────────
# MODULE 4: INVOICE GRID + REPORT
# ─────────────────────────────────────────
print("\n[4] INVOICES")
# Find invoice grid key
r_inv = session.get(BASE + "crm_invoice_grid.php")
for script in BeautifulSoup(r_inv.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        for m in re.finditer(r'data\.(\w+)\s*=\s*["\']1["\']', script.string):
            key = m.group(1)
            if key not in ['clientAllData']:
                r_try = session.post(BASE + "crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
                try:
                    j = r_try.json()
                    total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
                    if total > 0:
                        print(f"  Found invoice grid with key: {key}, total={total}")
                        inv_data = pull_ajax_grid(key=key, key_val="1", label="Invoices")
                        save("invoices", inv_data)
                        break
                except: pass

# Invoice Report (HTML)
print("  Trying Invoice Report page...")
inv_report = scrape_table_page(BASE + "crm_invoice_report.php")
if inv_report:
    save("invoice_report", inv_report)

# ─────────────────────────────────────────
# MODULE 5: PURCHASE ORDERS
# ─────────────────────────────────────────
print("\n[5] PURCHASE ORDERS")
r_po = session.get(BASE + "crm_general_po_grid.php")
for script in BeautifulSoup(r_po.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        for m in re.finditer(r'data\.(\w+)\s*=\s*["\']1["\']', script.string):
            key = m.group(1)
            r_try = session.post(BASE + "crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
            try:
                j = r_try.json()
                total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
                if total > 0:
                    print(f"  Found PO grid with key: {key}, total={total}")
                    po_data = pull_ajax_grid(key=key, key_val="1", label="Purchase Orders")
                    save("purchase_orders", po_data)
                    break
            except: pass

# ─────────────────────────────────────────
# MODULE 6: GRN (Goods Receipt)
# ─────────────────────────────────────────
print("\n[6] GRN (Goods Receipt Notes)")
r_grn = session.get(BASE + "crm_grn_grid.php")
for script in BeautifulSoup(r_grn.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        for m in re.finditer(r'data\.(\w+)\s*=\s*["\']1["\']', script.string):
            key = m.group(1)
            r_try = session.post(BASE + "crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
            try:
                j = r_try.json()
                total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
                if total > 0:
                    print(f"  Found GRN grid with key: {key}, total={total}")
                    grn_data = pull_ajax_grid(key=key, key_val="1", label="GRN")
                    save("grn", grn_data)
                    break
            except: pass

# GRN Report
grn_report = scrape_table_page(BASE + "crm_grn_report.php")
if grn_report:
    save("grn_report", grn_report)

# ─────────────────────────────────────────
# MODULE 7: PRODUCTION — WORK ORDERS
# ─────────────────────────────────────────
print("\n[7] PRODUCTION — WORK ORDERS")
r_wo = session.get(BASE + "crm_order_slip_grid.php")
for script in BeautifulSoup(r_wo.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        for m in re.finditer(r'data\.(\w+)\s*=\s*["\']1["\']', script.string):
            key = m.group(1)
            r_try = session.post(BASE + "crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
            try:
                j = r_try.json()
                total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
                if total > 0:
                    print(f"  Found Work Order grid with key: {key}, total={total}")
                    wo_data = pull_ajax_grid(key=key, key_val="1", label="Work Orders")
                    save("work_orders", wo_data)
                    break
            except: pass

# ─────────────────────────────────────────
# MODULE 8: PRODUCTION — GI PRODUCTION LOG
# ─────────────────────────────────────────
print("\n[8] GI PRODUCTION LOG")
r_gi = session.get(BASE + "crm_production_log_grid.php")
for script in BeautifulSoup(r_gi.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        for m in re.finditer(r'data\.(\w+)\s*=\s*["\']1["\']', script.string):
            key = m.group(1)
            r_try = session.post(BASE + "crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
            try:
                j = r_try.json()
                total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
                if total > 0:
                    print(f"  Found GI Production Log with key: {key}, total={total}")
                    gi_data = pull_ajax_grid(key=key, key_val="1", label="GI Prod Log")
                    save("gi_production_log", gi_data)
                    break
            except: pass

# ─────────────────────────────────────────
# MODULE 9: PACKING LOG
# ─────────────────────────────────────────
print("\n[9] PACKING LOG")
r_pk = session.get(BASE + "crm_packing_log_grid.php")
for script in BeautifulSoup(r_pk.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        for m in re.finditer(r'data\.(\w+)\s*=\s*["\']1["\']', script.string):
            key = m.group(1)
            r_try = session.post(BASE + "crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
            try:
                j = r_try.json()
                total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
                if total > 0:
                    print(f"  Found Packing Log with key: {key}, total={total}")
                    pk_data = pull_ajax_grid(key=key, key_val="1", label="Packing Log")
                    save("packing_log", pk_data)
                    break
            except: pass

# ─────────────────────────────────────────
# MODULE 10: ALL REPORTS (HTML-based)
# ─────────────────────────────────────────
print("\n[10] REPORTS (HTML)")
reports = {
    "so_pending_workorder":   "crm_get_pending_so_workorder.php",
    "pending_order_ppc":      "crm_pending_order_report_test.php",
    "daily_so_booked":        "crm_daily_so_booked_report.php",
    "pending_dispatch":       "crm_pending_dispatch_sales_person_report.php",
    "do_logistic":            "crm_do_logistic_salesperson_report.php",
    "pending_orders_sales":   "crm_pending_order_sales_person_report.php",
    "dispatched_report":      "crm_complete_dispatch_report.php",
    "enquiry_dashboard":      "crm_enquiry_dashboard.php",
    "endtoend_purchase":      "crm_endtoend_purchase_report.php",
}
for name, page in reports.items():
    result = scrape_table_page(BASE + page)
    if result and any(r['rows'] for r in result):
        total_rows = sum(len(r['rows']) for r in result)
        print(f"  {name}: {total_rows} rows found")
        save(f"report_{name}", result)
    else:
        print(f"  {name}: no static data (likely AJAX-loaded)")

# ─────────────────────────────────────────
# MODULE 11: RMS GRID — try all key patterns
# ─────────────────────────────────────────
print("\n[11] RMS (Raw Material Specifications)")
# Already found: data.rmsgrid = "1" but returns 0 records
# Try with date filters
for min_d, max_d in [("",""), ("01-01-2020","31-12-2026")]:
    r_rms = session.post(BASE + "crm_ajax.php", data={
        "draw":"1","start":"0","length":"50","search[value]":"",
        "order[0][column]":"0","order[0][dir]":"desc",
        "min": min_d, "max": max_d,
        "rmsgrid": "1"
    })
    try:
        j = r_rms.json()
        total = int(j.get('recordsTotal') or j.get('iTotalRecords') or 0)
        if total > 0:
            rms_data = pull_ajax_grid(key="rmsgrid", key_val="1",
                                      date_params={"min":min_d,"max":max_d}, label="RMS")
            save("rms_specs", rms_data)
            break
    except: pass
else:
    print("  RMS: 0 records (possibly user-restricted). Trying individual record fetch...")
    # Try to fetch known RMS record (ID 1799 found in browser URL earlier)
    for oid in [1799, 1800, 1798, 1, 100]:
        r2 = session.get(BASE + f"crm_rms_manage.php?function=2&orderid={oid}&type=view")
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        inputs = {inp.get('name'):inp.get('value','') for inp in soup2.find_all('input') if inp.get('name') and inp.get('value')}
        if len(inputs) > 5:
            print(f"  Found RMS record {oid}: {list(inputs.keys())[:10]}")
            save(f"rms_record_{oid}", inputs)

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
print("\n" + "="*70)
print("SCRAPE COMPLETE — Files saved in ./erp_data/")
files = os.listdir(OUTPUT_DIR)
for f in sorted(files):
    path = f"{OUTPUT_DIR}/{f}"
    with open(path) as fh:
        data = json.load(fh)
    count = len(data) if isinstance(data, list) else "dict"
    size  = os.path.getsize(path)
    print(f"  {f}: {count} records ({size:,} bytes)")
