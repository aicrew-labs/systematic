import requests
from bs4 import BeautifulSoup
import re, json

session = requests.Session()
session.post("https://systematic.ominfo.in/erp/crm_login.php", 
             data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)
BASE = "https://systematic.ominfo.in/erp/"

# ===== 1. CUSTOMER SEARCH API =====
# GET web_crm.php?searchData=<name>  
# Returns HTML with getCustomerDetails(id, name, phone, companyId)
print("="*60)
print("1. CUSTOMER SEARCH API DISCOVERY")
print("   Endpoint: GET web_crm.php?searchData=<text>")
print("   Returns: Customer ID, Name, Phone, Company ID")
print()

# Search for common letters to get a broad list
all_customers = {}
for letter in ['a', 'b', 'c', 'k', 'p', 's', 't', 'v', 'n', 'm', 'r', 'l']:
    r = session.get(BASE + f"web_crm.php?searchData={letter}")
    soup = BeautifulSoup(r.text, 'html.parser')
    for span in soup.find_all('span', class_='result1'):
        onclick = span.get('onclick', '')
        m = re.search(r"getCustomerDetails\((\d+),'([^']+)','([^']+)','([^']+)'\)", onclick)
        if m:
            cid, name, phone, cmpid = m.groups()
            all_customers[cid] = {"id": cid, "name": name, "phone": phone, "company_id": cmpid}

print(f"Total unique customers found: {len(all_customers)}")
print("Sample customers:")
for cid, c in list(all_customers.items())[:10]:
    print(f"  ID={cid}: {c['name']} | Phone: {c['phone']}")

# ===== 2. GET CUSTOMER DETAILS =====
print("\n" + "="*60)
print("2. CUSTOMER DETAIL LOOKUP")
print("   Endpoint: POST crm_ajax.php with custOverAllData=1, cust_id=<id>")
print()
# Try first customer
first_cid = list(all_customers.keys())[0]
first_cmpid = list(all_customers.values())[0]['company_id']
r2 = session.post(BASE + "crm_ajax.php", data={
    "custOverAllData": "1",
    "company_id": first_cmpid,
    "cust_id": first_cid
})
try:
    j = r2.json()
    print(f"Customer detail response keys: {list(j.keys())}")
    for key, val in j.items():
        if isinstance(val, list) and val:
            print(f"\n  [{key}] - {len(val)} items. First item keys: {list(val[0].keys()) if isinstance(val[0], dict) else 'not dict'}")
            if isinstance(val[0], dict):
                print(f"  First item: {json.dumps(val[0], indent=4, default=str)[:400]}")
        else:
            print(f"\n  [{key}]: {str(val)[:200]}")
except:
    print("Not JSON. Raw:", r2.text[:600])

# ===== 3. SO REPORT =====
print("\n" + "="*60)
print("3. SALES ORDER REPORT")
r3 = session.get(BASE + "crm_so_report.php")
soup3 = BeautifulSoup(r3.text, 'html.parser')
for t in soup3.find_all('table'):
    rows = [r for r in t.find_all('tr') if r.find('td')]
    real = [r for r in rows if any(td.get_text(strip=True) and td.get_text(strip=True) != '--' for td in r.find_all('td'))]
    if real:
        print(f"SO Report table: {len(real)} real rows")
        for row in real[:3]:
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            print(f"  {cells[:8]}")
        break
