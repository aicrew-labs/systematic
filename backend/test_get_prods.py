import requests, json
s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})

so_data = json.load(open('c:/Personal/Projects/systematic/systematic/erp_data/sales_orders.json'))

for so in so_data[:5]:
    oid = so['order_id']
    res = s.post('https://systematic.ominfo.in/erp/web_crm.php', data={'action': 'getcyncustdata', 'order_id': oid})
    try:
        j = res.json()
        prods = [p['prod_code'] for p in j.get('products', [])]
        print(f"Order {oid}: {prods}")
    except Exception as e:
        print(f"Order {oid} error:", e, res.text[:100])
