import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import supabase

def main():
    print("INSIDE CUSTOMERS:")
    c_res = supabase.table("customers").select("id, name").ilike("name", "%POLYCAB%DAMAN%").execute()
    for c in c_res.data:
        name = c['name']
        print(f"ID {c['id']}: len={len(name)}, chars={[ord(x) for x in name]}, repr={repr(name)}")
        
    print("\nINSIDE INVOICES:")
    i_res = supabase.table("invoices").select("id, customer_name").ilike("customer_name", "%POLYCAB%DAMAN%").limit(5).execute()
    for i in i_res.data:
        name = i['customer_name']
        print(f"Inv {i['id']}: len={len(name)}, chars={[ord(x) for x in name]}, repr={repr(name)}")

if __name__ == '__main__':
    main()
