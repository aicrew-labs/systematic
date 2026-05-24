import sys
from bs4 import BeautifulSoup

path = 'c:/Personal/Projects/systematic/systematic/erp_data/so_detail_4305.html'
with open(path, encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

tables = soup.find_all('table')
print(f'Total tables: {len(tables)}')

for i, t in enumerate(tables):
    rows = t.find_all('tr')
    print(f'\nTable {i} rows: {len(rows)}')
    for j, tr in enumerate(rows):
        tds = [td.get_text(strip=True).replace('\n', ' ') for td in tr.find_all(['td', 'th'])]
        # only print non-empty rows
        if any(tds):
            print(f'  Row {j}: {tds}')
        if j > 25:
            print("  ... truncating")
            break
