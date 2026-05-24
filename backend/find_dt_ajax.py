import requests, re
s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})
html=s.get('https://systematic.ominfo.in/erp/crm_invoice_grid.php').text
# Find DataTable ajax url
m = re.search(r'ajax.*?url\s*:\s*[\'\"]([^\'\"]+)[\'\"]', html, flags=re.DOTALL|re.IGNORECASE)
if m:
    print('DataTable AJAX URL:', m.group(1))
else:
    print('DataTable not found in JS')
