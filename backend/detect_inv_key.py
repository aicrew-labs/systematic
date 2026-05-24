import requests, re
from bs4 import BeautifulSoup

s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})
r_inv = s.get('https://systematic.ominfo.in/erp/crm_invoice_grid.php')

for script in BeautifulSoup(r_inv.text, 'html.parser').find_all('script'):
    if script.string and 'crm_ajax.php' in script.string:
        print("Found crm_ajax.php script snippet!")
        matches = re.findall(r'data\.([A-Za-z0-9_]+)\s*=\s*[\'\"]1[\'\"]', script.string)
        print("Detected keys:", matches)
