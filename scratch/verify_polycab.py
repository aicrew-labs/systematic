import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import supabase

def main():
    print("Checking database for POLYCAB INDIA LIMITED-DAMAN - CENTRAL STORE...")
    cust_res = supabase.table("customers").select("id, name, total_orders").eq("id", 1776).execute()
    print("Customer entry:", cust_res.data)
    
    # Check linked invoices
    inv_res = supabase.table("invoices").select("id, customer_name, customer_id").eq("customer_id", 1776).limit(5).execute()
    print(f"Number of linked invoices retrieved: {len(inv_res.data)}")
    for inv in inv_res.data:
        print(f"  - Invoice ID: {inv['id']}, Name: {inv['customer_name']}, Linked Customer ID: {inv['customer_id']}")
        
    # Count total linked invoices for this customer
    count_res = supabase.table("invoices").select("id", count="exact").eq("customer_id", 1776).execute()
    print(f"Total linked invoices in DB: {count_res.count}")

if __name__ == '__main__':
    main()
