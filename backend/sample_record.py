import requests
import json
import os

BASE = "https://systematic.ominfo.in/erp/"
session = requests.Session()
session.post(BASE + "crm_login.php", data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)

# Let's get one record from crm_sales_order_grid
print("=== SALES ORDER GRID RECORD ===")
with open('c:/Personal/Projects/systematic/systematic/erp_data/sales_orders.json', 'r') as f:
    so_list = json.load(f)
    sample_so = so_list[0]
    for key, val in sample_so.items():
        if key == 'order':
            print(f"\n[order] field breakdown (split by '*'):")
            parts = str(val).split('*')
            for i, p in enumerate(parts):
                print(f"  Index {i}: {p}")
        else:
            print(f"{key}: {val}")


# Let's also fetch crm_invoice_grid.php
print("\n=== INVOICE GRID RECORD ===")
try:
    r = session.get(BASE + "web_crm.php?getinvoicelist=1&status=1", timeout=10) # this is a guess for the endpoint
    if r.status_code == 200:
        inv_data = r.json()
        if inv_data:
            sample_inv = inv_data[0]
            for key, val in sample_inv.items():
                if key == 'order':
                    print(f"\n[order] field breakdown (split by '*'):")
                    parts = str(val).split('*')
                    for i, p in enumerate(parts):
                        print(f"  Index {i}: {p}")
                else:
                    print(f"{key}: {val}")
        else:
            print("No invoice records returned.")
except Exception as e:
    print(f"Could not fetch invoices directly: {e}")
