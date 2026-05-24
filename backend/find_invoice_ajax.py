import requests
from bs4 import BeautifulSoup

s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})
html=s.get('https://systematic.ominfo.in/erp/crm_invoice_grid.php').text
soup = BeautifulSoup(html, 'html.parser')
for script in soup.find_all('script'):
    if script.string and 'ajax' in script.string:
        print(script.string[:1000])
