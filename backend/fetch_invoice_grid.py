import requests, json

s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})

# Fetch a couple of invoice records
r = s.post('https://systematic.ominfo.in/erp/crm_ajax.php', data={
    'draw':'1', 'start':'0', 'length':'5', 'search[value]':'', 'invoicegrid':'1',
    'min': '01-01-2020', 'max': '31-12-2026'
})

data = r.json()
print("Total records:", data.get('recordsTotal'))
records = data.get('data', [])

if records:
    print("\nKeys:", list(records[0].keys()))
    print("\nFirst record:", records[0])
else:
    print("No records found.")
