import sys
sys.path.insert(0, 'backend')
from app.database import supabase

product_id = 153

# Get the cost_category_code for this product
resp = supabase.table('products').select('id, product_type, cost_category_code').eq('id', product_id).execute()
print('Product info:')
for r in resp.data or []:
    print(f'  id={r["id"]}  type={r["product_type"]}  cat={r["cost_category_code"]}')
cat_code = (resp.data or [{}])[0].get('cost_category_code')
print(f'\ncost_category_code = {cat_code}')

if not cat_code:
    print('No category assigned - this is why the competitiveness check finds no peers!')
else:
    # All invoices on 15th May in same category
    resp2 = supabase.table('invoices').select('*, products!inner(cost_category_code)').eq('products.cost_category_code', cat_code).eq('invoice_date', '2026-05-15').execute()
    print(f'\nAll invoices on 2026-05-15 in category {cat_code}: {len(resp2.data or [])}')
    for r in resp2.data or []:
        print(f'  customer={r["customer_name"]}  prod={r["prod_code"]}  rate={r["unit_rate"]}')
