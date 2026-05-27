import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import supabase

def main():
    print("Checking for invoices with NULL customer_id...")
    res = supabase.table("invoices").select("id, customer_name").is_("customer_id", "null").execute()
    invoices = res.data or []
    print(f"Found {len(invoices)} invoices with NULL customer_id.")
    
    if not invoices:
        return
        
    print("\nFetching all customers for mapping...")
    cust_res = supabase.table("customers").select("id, name").execute()
    cust_map = {c["name"].strip().lower(): c["id"] for c in cust_res.data or []}
    print(f"Loaded {len(cust_map)} customers from database.")
    
    match_count = 0
    unmatched_names = set()
    
    for inv in invoices:
        name = inv.get("customer_name")
        if not name:
            continue
        cleaned_name = name.strip().lower()
        if cleaned_name in cust_map:
            match_count += 1
        else:
            unmatched_names.add(name)
            
    print(f"Out of {len(invoices)} NULL-ID invoices, {match_count} can be matched directly by name.")
    print(f"Unique unmatched customer names ({len(unmatched_names)}):")
    for name in sorted(list(unmatched_names))[:20]:
        print(f"  - {repr(name)}")

if __name__ == '__main__':
    main()
