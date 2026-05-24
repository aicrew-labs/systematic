import requests
from bs4 import BeautifulSoup

BASE = "https://systematic.ominfo.in/erp/"
session = requests.Session()
session.post(BASE + "crm_login.php", data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)

r = session.get(BASE + "crm_sales_order_grid.php")
soup = BeautifulSoup(r.text, 'html.parser')

links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    text = a.get_text(strip=True)
    if 'php' in href:
        links.append(f"{text}: {href}")

for l in sorted(list(set(links))):
    print(l)
