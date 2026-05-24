"""
Diagnostic: Find correct SO detail page URL and fix order field parsing.
Run: python backend/diagnose_so.py
"""
import requests, json, os, re
from bs4 import BeautifulSoup

BASE = "https://systematic.ominfo.in/erp/"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "erp_data")

session = requests.Session()
session.post(BASE + "crm_login.php", data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)

# Load SO list
with open(os.path.join(OUTPUT_DIR, "sales_orders.json")) as f:
    so_list = json.load(f)

sample = so_list[0]
order_field = sample.get('order', '')
parts = order_field.split('*')
print(f"Order field: {order_field}")
print(f"Parts: {parts}")
for i, p in enumerate(parts):
    print(f"  [{i}]: {p}")

order_id = sample.get('order_id')
print(f"\norder_id: {order_id}")

# Try many URL patterns to find SO detail page
patterns = [
    f"crm_so_manage.php?function=2&orderid={order_id}&type=view",
    f"crm_sales_order_manage.php?function=2&orderid={order_id}",
    f"crm_so_manage.php?orderid={order_id}&type=view",
    f"crm_so_view.php?orderid={order_id}",
    f"crm_so_manage.php?id={order_id}",
    f"crm_sales_order.php?id={order_id}",
    f"view_so.php?id={order_id}",
    f"crm_so.php?function=2&orderid={order_id}",
]

for pat in patterns:
    r = session.get(BASE + pat)
    body = r.text[:200].replace('\n', ' ')
    print(f"\nURL: {pat}")
    print(f"  Status: {r.status_code}, Length: {len(r.text)}, Preview: {body[:100]}")
    if r.status_code == 200 and len(r.text) > 1000 and 'login' not in r.text.lower()[:200]:
        print("  >>> PROMISING! Saving full response.")
        with open(os.path.join(OUTPUT_DIR, f"so_detail_{order_id}.html"), "w", encoding='utf-8', errors='ignore') as f:
            f.write(r.text)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tbl in soup.find_all('table'):
            ths = [th.get_text(strip=True) for th in tbl.find_all('th')]
            if ths:
                print(f"  Table headers: {ths}")

# Also try the sales order grid page itself to find embedded links/patterns
print("\n--- Checking SO grid page for detail links ---")
r = session.get(BASE + "crm_sales_order_grid.php")
soup = BeautifulSoup(r.text, 'html.parser')
# Find any JS functions that handle row clicks / view actions
for script in soup.find_all('script'):
    if script.string and ('function' in script.string or 'orderid' in script.string.lower()):
        print(f"Script snippet: {script.string[:500]}")
        print("---")

# Also check the 'order' column format in the AJAX data - look for view URL
print("\n--- Sample 'order' field analysis ---")
for so in so_list[:5]:
    parts = so.get('order', '').split('*')
    print(f"  Customer: {so.get('company_name')} | Qty: {so.get('total_qty')} | Amount(idx6): {parts[6] if len(parts)>6 else 'N/A'} | Amount(idx7): {parts[7] if len(parts)>7 else 'N/A'}")
