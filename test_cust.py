import requests, re
from bs4 import BeautifulSoup

session = requests.Session()
session.post("https://systematic.ominfo.in/erp/crm_login.php", data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)

r = session.get("https://systematic.ominfo.in/erp/crm_customer_grid.php")
for s in BeautifulSoup(r.text, 'html.parser').find_all('script'):
    if s.string and 'crm_ajax.php' in s.string:
        for m in re.finditer(r'data\.(\w+)\s*=\s*["\']1["\']', s.string):
            key = m.group(1)
            print("Found potential key:", key)
            if key != 'clientAllData':
                r_try = session.post("https://systematic.ominfo.in/erp/crm_ajax.php", data={"draw":"1","start":"0","length":"5","search[value]":"", key:"1"})
                try:
                    j = r_try.json()
                    print(f"Key {key} returned {j.get('recordsTotal', 0)} total records")
                except Exception as e:
                    print("Error parsing json for key", key, ":", e)
