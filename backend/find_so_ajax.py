import requests
from bs4 import BeautifulSoup
import re

s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})
html=s.get('https://systematic.ominfo.in/erp/crm_sales_order_manage.php?function=2&orderno=4305&type=1').text
soup = BeautifulSoup(html, 'html.parser')
for script in soup.find_all('script'):
    if script.string and 'ajax' in script.string:
        matches = re.findall(r'url[\s:]+[\'\"]([^\'\"]+)[\'\"]', script.string)
        if matches:
            print(matches)
