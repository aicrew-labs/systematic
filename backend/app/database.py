import json
import os
from typing import List, Dict, Any

# Assuming backend/app/database.py is run with CWD at the project root
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "erp_data")

def load_json(filename: str) -> List[Dict[str, Any]]:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: Data file {filename} not found at {path}")
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

# Load data into memory (In a real app, this might use a cache/DB)
CUSTOMERS = load_json("customers.json")
ENQUIRIES = load_json("enquiries.json")
INVOICES = load_json("invoices.json")
RMS_SPECS = load_json("rms_specs.json")
PENDING_ORDERS = load_json("pending_orders.json")

# Create quick lookup dicts
CUSTOMER_MAP = {c.get("customer_id", c.get("cliid", "")): c for c in CUSTOMERS}

# Get distinct product types/codes from RMS
PRODUCTS = []
_seen_prods = set()
for r in RMS_SPECS:
    ptype = r.get("product_type", "").strip()
    pcode = r.get("order_no", "").strip()
    if ptype and pcode and pcode not in _seen_prods:
        PRODUCTS.append({"product_type": ptype, "product_code": pcode})
        _seen_prods.add(pcode)

# Get daily rates (in-memory for now, could be saved to a small file)
# Default values
DAILY_RATES = {
    "steel_ms_rate": 45000.0, # Per MT
    "steel_hc_rate": 48000.0,
    "zinc_rate": 250.0        # Per KG
}

def get_customers() -> List[Dict]:
    return [{"customer_id": c.get("cliid", ""), "name": c.get("cliname", "")} for c in CUSTOMERS if c.get("cliname")]

def get_products() -> List[Dict]:
    return PRODUCTS

def get_historical_enquiries(customer_id: str = None, product_code: str = None) -> List[Dict]:
    results = ENQUIRIES
    if customer_id:
        results = [r for r in results if r.get("cust_id") == customer_id or str(r.get("cust_id")) == str(customer_id)]
    if product_code:
        # Match product name roughly
        product_code_lower = product_code.lower()
        results = [r for r in results if product_code_lower in r.get("enq_no", "").lower() or product_code_lower in r.get("quote_no", "").lower()] # We might need better matching
    return results

def get_historical_invoices(customer_name: str = None, product_code: str = None) -> List[Dict]:
    results = INVOICES
    if customer_name:
        results = [r for r in results if customer_name.lower() in r.get("cust_name", "").lower()]
    if product_code:
        results = [r for r in results if product_code.lower() in r.get("prod_code", "").lower()]
    return results

def update_daily_rates(rates: dict):
    global DAILY_RATES
    DAILY_RATES.update(rates)
    return DAILY_RATES

def get_daily_rates() -> dict:
    return DAILY_RATES
