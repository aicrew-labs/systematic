import requests
from bs4 import BeautifulSoup

BASE = "https://systematic.ominfo.in/erp/"
ORDER_ID = "4305"  # Sample order ID
URL = f"{BASE}crm_sales_order_manage.php?function=2&orderno={ORDER_ID}&type=1"

session = requests.Session()
# Login first
session.post(BASE + "crm_login.php", data={"emailid": "SYS079", "psw": "5651"}, allow_redirects=True)

# Fetch detail page
print(f"Fetching SO Detail: {URL}")
r = session.get(URL)

soup = BeautifulSoup(r.text, 'html.parser')
for i, tbl in enumerate(soup.find_all('table')):
    ths = [th.get_text(strip=True) for th in tbl.find_all('th')]
    if 'Product' in ths and 'Quantity' in ths and 'Unit Rate' in ths:
        print(f"\n--- FOUND LINE ITEM TABLE (Table {i}) ---")
        print(f"Headers: {ths}")
        
        # Iterate over all rows in this table
        for r_idx, row in enumerate(tbl.find_all('tr')):
            cells = [td.get_text(strip=True) for td in row.find_all('td')]
            if cells:
                print(f"Row {r_idx}: {cells}")
        
        # Also check if there are inputs inside the tds (sometimes data is in value attributes)
        print("\n--- Checking for input values in the rows ---")
        for r_idx, row in enumerate(tbl.find_all('tr')):
            cells = []
            for td in row.find_all('td'):
                # Try getting value of input or textarea
                input_tag = td.find(['input', 'textarea', 'select'])
                if input_tag and input_tag.has_attr('value'):
                    cells.append(input_tag['value'])
                elif input_tag and input_tag.name == 'textarea':
                    cells.append(input_tag.get_text(strip=True))
                elif input_tag and input_tag.name == 'select':
                    selected = input_tag.find('option', selected=True)
                    if selected:
                        cells.append(selected.get_text(strip=True))
                    else:
                        cells.append(td.get_text(strip=True))
                else:
                    cells.append(td.get_text(strip=True))
            if any(cells):
                print(f"Row {r_idx} (Inputs): {cells}")
