import requests
s=requests.Session()
s.post('https://systematic.ominfo.in/erp/crm_login.php', data={'emailid': 'SYS079', 'psw': '5651'})
for a in ['get_so_details', 'getSalesOrderDetails', 'getorderdetails', 'getinvoicedetails', 'get_invoice_details']:
    res = s.post('https://systematic.ominfo.in/erp/web_crm.php', data={'action': a, 'order_id': 4305})
    print(f"{a}: {res.text[:100]}")
