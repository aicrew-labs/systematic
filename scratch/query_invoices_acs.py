import requests, json

headers = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJnY2NxaHNma3hnaGNhZXRqbmdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMTY5OCwiZXhwIjoyMDk0Njc3Njk4fQ.8_6Gn7fYrSj0JQYg9LP87coNnf3IgGW2h8mybghEcS0',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJnY2NxaHNma3hnaGNhZXRqbmdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMTY5OCwiZXhwIjoyMDk0Njc3Njk4fQ.8_6Gn7fYrSj0JQYg9LP87coNnf3IgGW2h8mybghEcS0'
}

# 1. Fetch ACS products
url1 = 'https://bgccqhsfkxghcaetjngc.supabase.co/rest/v1/products?select=id,display_name&product_type=eq.ACS'
res1 = requests.get(url1, headers=headers)
ids = [str(p['id']) for p in res1.json()]

if not ids:
    print("[]")
else:
    # 2. Fetch invoices for these products
    url2 = f"https://bgccqhsfkxghcaetjngc.supabase.co/rest/v1/invoices?select=customer_name,invoice_date,quantity,prod_code&product_id=in.({','.join(ids)})"
    res2 = requests.get(url2, headers=headers)
    print(json.dumps(res2.json(), indent=2))
