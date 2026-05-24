import requests, re
s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})
html=s.get('https://systematic.ominfo.in/erp/crm_invoice_grid.php').text
# Find all ajax URLs
matches = re.findall(r'url\s*:\s*[\'\"]([^\'\"]+)[\'\"]', html)
print('All URLs in JS:', matches)
