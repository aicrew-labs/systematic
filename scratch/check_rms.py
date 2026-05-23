"""Scratch helper used during debugging — pulls RMS grid HTML from the ERP.

Set ERP_USER and ERP_PASS in your .env before running.
"""
import os
import re

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

ERP_USER = os.getenv("ERP_USER")
ERP_PASS = os.getenv("ERP_PASS")
if not ERP_USER or not ERP_PASS:
    raise SystemExit("ERP_USER and ERP_PASS must be set in .env to run this scratch helper.")

BASE = "https://systematic.ominfo.in/erp/"
session = requests.Session()
session.post(BASE + "crm_login.php",
             data={"emailid": ERP_USER, "psw": ERP_PASS}, allow_redirects=True)

r = session.get(BASE + "crm_rms_grid.php")
soup = BeautifulSoup(r.text, "html.parser")

print("\n--- Columns definition ---")
for script in soup.find_all("script"):
    if script.string and "order-grid-table" in script.string:
        match = re.search(r'"columns"\s*:\s*\[(.*?)\]', script.string, re.DOTALL)
        if match:
            print(match.group(0))
        else:
            idx = script.string.find("order-grid-table")
            print(script.string[idx:idx + 1500])
