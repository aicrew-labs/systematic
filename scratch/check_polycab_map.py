import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import supabase

def main():
    print("Fetching customer from database...")
    cust_res = supabase.table("customers").select("id, name").ilike("name", "%POLYCAB%DAMAN%").execute()
    print("Customers in DB:")
    for c in cust_res.data:
        print(f"  - ID: {c['id']}, Name: {repr(c['name'])}")
        
    print("\nFetching unique customer_names from invoices table containing 'POLYCAB' and 'DAMAN'...")
    inv_res = supabase.table("invoices").select("customer_name").ilike("customer_name", "%POLYCAB%DAMAN%").limit(100).execute()
    names = set(inv['customer_name'] for inv in inv_res.data if inv.get('customer_name'))
    for n in names:
        print(f"  - Name in invoices: {repr(n)}")

if __name__ == '__main__':
    main()
