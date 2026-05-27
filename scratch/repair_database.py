import sys
import os
from collections import defaultdict

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import supabase
from supabase_etl import _canon_type, _extract_size_mm

def fetch_all(table: str, columns: str, filter_col: str = None, filter_val: str = None, batch: int = 1000) -> list[dict]:
    """Fetch rows in batches to bypass Supabase's default 1000 limit."""
    rows = []
    start = 0
    while True:
        query = supabase.table(table).select(columns)
        if filter_col and filter_val is not None:
            if filter_val == "null":
                query = query.is_(filter_col, "null")
            else:
                query = query.eq(filter_col, filter_val)
        
        res = query.range(start, start + batch - 1).execute()
        if not res.data:
            break
        rows.extend(res.data)
        if len(res.data) < batch:
            break
        start += batch
    return rows

def build_product_resolver():
    """Loads ALL products into memory and returns a resolver."""
    products = fetch_all("products", "id, product_type, size_mm, size_label")
    buckets = {}
    for p in products:
        canon = _canon_type(p.get("product_type") or "") or _canon_type(p.get("size_label") or "")
        if canon:
            buckets.setdefault(canon, []).append(p)
            
    print(f"  Product resolver: {len(products)} products bucketed into {len(buckets)} canonical types")
    
    def resolve(text: str) -> int | None:
        if not text:
            return None
        canon = _canon_type(text)
        size = _extract_size_mm(text)
        if not canon or size is None:
            return None
        candidates = buckets.get(canon, [])
        best = None
        best_diff = 0.06
        for p in candidates:
            psize = p.get("size_mm")
            if psize is None:
                continue
            d = abs(psize - size)
            if d < best_diff:
                best = p
                best_diff = d
        return best["id"] if best else None
        
    return resolve

def main():
    print("=" * 60)
    print("Quote Intelligence - In-Place Database FK Repair Script")
    print("=" * 60)
    
    # 1. Fetch all customers to build complete customer_map
    print("\nFetching all customers...")
    customers = fetch_all("customers", "id, name")
    customer_map = {c["name"].strip().lower(): c["id"] for c in customers}
    print(f"Loaded {len(customer_map)} customers.")
    
    # 2. Build complete product resolver
    print("\nBuilding product resolver...")
    resolve_product = build_product_resolver()
    
    # 3. Repair invoices
    print("\nRepairing invoices...")
    null_cust_inv = fetch_all("invoices", "id, customer_name", "customer_id", "null")
    print(f"Found {len(null_cust_inv)} invoices with NULL customer_id.")
    
    # Group invoice IDs by resolved customer_id
    cust_updates = defaultdict(list)
    for inv in null_cust_inv:
        name = inv.get("customer_name")
        if name:
            cid = customer_map.get(name.strip().lower())
            if cid:
                cust_updates[cid].append(inv["id"])
                
    # Apply updates in bulk
    resolved_cust_count = 0
    for cid, ids in cust_updates.items():
        for i in range(0, len(ids), 200):
            chunk = ids[i:i+200]
            supabase.table("invoices").update({"customer_id": cid}).in_("id", chunk).execute()
        resolved_cust_count += len(ids)
    print(f"  -> Successfully linked {resolved_cust_count} invoices to customer_ids.")
    
    # Repair invoice product_ids
    null_prod_inv = fetch_all("invoices", "id, prod_code", "product_id", "null")
    print(f"Found {len(null_prod_inv)} invoices with NULL product_id.")
    prod_updates = defaultdict(list)
    for inv in null_prod_inv:
        prod_text = inv.get("prod_code")
        if prod_text:
            pid = resolve_product(prod_text)
            if pid:
                prod_updates[pid].append(inv["id"])
                
    resolved_prod_count = 0
    for pid, ids in prod_updates.items():
        for i in range(0, len(ids), 200):
            chunk = ids[i:i+200]
            supabase.table("invoices").update({"product_id": pid}).in_("id", chunk).execute()
        resolved_prod_count += len(ids)
    print(f"  -> Successfully linked {resolved_prod_count} invoices to product_ids.")
    
    # 4. Repair sales_orders
    print("\nRepairing sales_orders...")
    null_cust_so = fetch_all("sales_orders", "id, customer_name", "customer_id", "null")
    print(f"Found {len(null_cust_so)} sales_orders with NULL customer_id.")
    cust_so_updates = defaultdict(list)
    for so in null_cust_so:
        name = so.get("customer_name")
        if name:
            cid = customer_map.get(name.strip().lower())
            if cid:
                cust_so_updates[cid].append(so["id"])
                
    resolved_cust_so = 0
    for cid, ids in cust_so_updates.items():
        for i in range(0, len(ids), 200):
            chunk = ids[i:i+200]
            supabase.table("sales_orders").update({"customer_id": cid}).in_("id", chunk).execute()
        resolved_cust_so += len(ids)
    print(f"  -> Successfully linked {resolved_cust_so} sales_orders to customer_ids.")
    
    null_prod_so = fetch_all("sales_orders", "id, prod_code", "product_id", "null")
    print(f"Found {len(null_prod_so)} sales_orders with NULL product_id.")
    prod_so_updates = defaultdict(list)
    for so in null_prod_so:
        prod_text = so.get("prod_code")
        if prod_text:
            pid = resolve_product(prod_text)
            if pid:
                prod_so_updates[pid].append(so["id"])
                
    resolved_prod_so = 0
    for pid, ids in prod_so_updates.items():
        for i in range(0, len(ids), 200):
            chunk = ids[i:i+200]
            supabase.table("sales_orders").update({"product_id": pid}).in_("id", chunk).execute()
        resolved_prod_so += len(ids)
    print(f"  -> Successfully linked {resolved_prod_so} sales_orders to product_ids.")
    
    # 5. Repair enquiries
    print("\nRepairing enquiries...")
    null_cust_enq = fetch_all("enquiries", "id, customer_name", "customer_id", "null")
    print(f"Found {len(null_cust_enq)} enquiries with NULL customer_id.")
    cust_enq_updates = defaultdict(list)
    for enq in null_cust_enq:
        name = enq.get("customer_name")
        if name:
            cid = customer_map.get(name.strip().lower())
            if cid:
                cust_enq_updates[cid].append(enq["id"])
                
    resolved_cust_enq = 0
    for cid, ids in cust_enq_updates.items():
        for i in range(0, len(ids), 200):
            chunk = ids[i:i+200]
            supabase.table("enquiries").update({"customer_id": cid}).in_("id", chunk).execute()
        resolved_cust_enq += len(ids)
    print(f"  -> Successfully linked {resolved_cust_enq} enquiries to customer_ids.")
    
    null_prod_enq = fetch_all("enquiries", "id, product_desc", "product_id", "null")
    print(f"Found {len(null_prod_enq)} enquiries with NULL product_id.")
    prod_enq_updates = defaultdict(list)
    for enq in null_prod_enq:
        prod_text = enq.get("product_desc")
        if prod_text:
            pid = resolve_product(prod_text)
            if pid:
                prod_enq_updates[pid].append(enq["id"])
                
    resolved_prod_enq = 0
    for pid, ids in prod_enq_updates.items():
        for i in range(0, len(ids), 200):
            chunk = ids[i:i+200]
            supabase.table("enquiries").update({"product_id": pid}).in_("id", chunk).execute()
        resolved_prod_enq += len(ids)
    print(f"  -> Successfully linked {resolved_prod_enq} enquiries to product_ids.")
    
    print("\nDatabase FK repair complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
