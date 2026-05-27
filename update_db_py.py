with open('backend/app/database.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = '''
def invoices_for_category(category_code: str, limit: int = 20) -> list[dict]:
    # We join with products to filter by cost_category_code
    resp = supabase.table("invoice_items").select("*, products!inner(*)").eq("products.cost_category_code", category_code).order("invoice_date", desc=True).limit(limit).execute()
    return resp.data or []
'''

if 'def invoices_for_category' not in content:
    content = content + '\n' + new_func
    with open('backend/app/database.py', 'w', encoding='utf-8') as f:
        f.write(content)
