import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import supabase

def main():
    print("Checking unique states in customers table...")
    res = supabase.table("customers").select("id, name").limit(10).execute()
    # Wait, we can't select arbitrary columns if they are not in schema. Let's see what columns are in customers table:
    # From supabase_schema.sql: id, name, phone, company_id, total_orders, total_qty_mt, dispatched_qty_mt, is_repeat, sales_rep
    # Wait! In the main dashboard, the state and city inputs are just text fields! E.g. <input type="text" id="custState" class="form-input">
    # Let's check customers table columns in database. Let's run a select on customers table to check if there is state/city.
    # Wait! In migration 007 or similar, is state/city added?
    # Let's read customers schema or metadata. Let's do a select * from customers limit 1.
    res = supabase.table("customers").select("*").limit(1).execute()
    print("Sample customer row:", res.data[0] if res.data else "No rows")

if __name__ == '__main__':
    main()
