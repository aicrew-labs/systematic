import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import supabase

def main():
    print("Searching for Polycab in invoices table by customer_name...")
    # Search for customer_name containing 'polycab' in invoices
    res = supabase.table("invoices").select("customer_name, customer_id, prod_code").ilike("customer_name", "%polycab%").limit(500).execute()
    
    print(f"Total matching invoice rows found in select: {len(res.data)}")
    
    # Aggregate counts by (customer_name, customer_id)
    counts = {}
    for inv in res.data:
        key = (inv.get("customer_name"), inv.get("customer_id"))
        counts[key] = counts.get(key, 0) + 1
        
    print("\nInvoice counts grouped by (customer_name, customer_id):")
    for (name, cid), count in counts.items():
        print(f"Name: '{name}', Customer ID in Invoice: {cid}, Count: {count}")
        
        # Verify if customer ID actually exists in customers table
        if cid:
            cust_check = supabase.table("customers").select("id, name").eq("id", cid).execute()
            if cust_check.data:
                print(f"  -> Matches Customer ID {cid} in customers table: '{cust_check.data[0]['name']}'")
            else:
                print(f"  -> WARNING: Customer ID {cid} DOES NOT EXIST in customers table!")
        else:
            print(f"  -> Customer ID is None!")

if __name__ == '__main__':
    main()
