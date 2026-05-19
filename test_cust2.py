import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.post("https://systematic.ominfo.in/erp/crm_login.php", data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)

r = session.get("https://systematic.ominfo.in/erp/crm_customer_grid.php")
print(r.text[:1000])

for s in BeautifulSoup(r.text, 'html.parser').find_all('script'):
    if 'data.' in s.text:
        print(s.text[:500])
