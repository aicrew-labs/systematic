import requests
import re

s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})
html=s.get('https://systematic.ominfo.in/erp/crm_invoice_grid.php').text
matches=re.findall(r'web_crm\.php\?[^\s\"\']+', html)
for m in set(matches):
    print(m)
