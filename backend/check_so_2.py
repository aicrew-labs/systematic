import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.post("https://systematic.ominfo.in/erp/crm_login.php", data={"emailid": "SYS079", "psw": "5651"})
r = session.get("https://systematic.ominfo.in/erp/crm_sales_order_manage.php?function=2&orderno=4261&type=1")
soup = BeautifulSoup(r.text, 'html.parser')

print("Fetching Order 4261...")
t = soup.find_all('table')[0]
rows = t.find_all('tr')
for j, tr in enumerate(rows):
    tds = [td.get_text(strip=True).replace('\n', ' ') for td in tr.find_all(['td', 'th'])]
    if any(tds):
        print(f"  Row {j}: {tds}")
    if j > 20: break
