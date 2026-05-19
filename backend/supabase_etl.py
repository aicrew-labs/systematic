"""
Supabase ETL Loader — Quote Intelligence
=========================================
Loads all scraped ERP data and master data into Supabase.

Usage:
    python3 backend/supabase_etl.py

Requirements:
    pip install supabase python-dateutil pandas openpyxl
"""

import json
import os
import sys
import random
from datetime import date, timedelta, datetime
from dateutil import parser as dateparser

# ── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://bgccqhsfkxghcaetjngc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJnY2NxaHNma3hnaGNhZXRqbmdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMTY5OCwiZXhwIjoyMDk0Njc3Njk4fQ.8_6Gn7fYrSj0JQYg9LP87coNnf3IgGW2h8mybghEcS0"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "erp_data")
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

from supabase import create_client, Client
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  ⚠️  {filename} not found, skipping.")
        return []
    with open(path) as f:
        return json.load(f)


def upsert_batch(table: str, rows: list, batch_size: int = 200, on_conflict: str = None):
    """Insert rows in batches, report count."""
    if not rows:
        print(f"  ⚠️  No rows to insert for {table}")
        return
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        if on_conflict:
            sb.table(table).upsert(batch, on_conflict=on_conflict).execute()
        else:
            sb.table(table).upsert(batch).execute()
        total += len(batch)
        print(f"  → {table}: {total}/{len(rows)} rows inserted", end="\r")
    print(f"  ✅ {table}: {total} rows inserted.          ")


# ─────────────────────────────────────────────────────────────────────────────
# 1. PRODUCTS
# ─────────────────────────────────────────────────────────────────────────────
def seed_products():
    print("\n📦 Seeding products...")
    rows = []

    ms_sizes = [
        1.10, 1.18, 1.25, 1.38, 1.45, 1.52, 1.58, 1.60, 1.70, 1.80,
        1.90, 2.00, 2.10, 2.12, 2.20, 2.23, 2.25, 2.28, 2.32, 2.38,
        2.42, 2.45, 2.49, 2.58, 2.60, 2.62, 2.70, 2.80, 2.90, 2.98,
        3.00, 3.13, 3.15, 3.94, 5.58, 6.00, 6.78, 7.78,
    ]
    for s in ms_sizes:
        rows.append(dict(product_type="MS Wire", size_mm=s, size_label=f"{s:.2f} MM",
                         grade="IS 7887 G-4", unit_of_measure="MT",
                         display_name=f"MS Wire {s:.2f}mm", hsn_code="722990", gst_pct=18.0))

    for s in [4.90, 5.10, 5.68]:
        rows.append(dict(product_type="HC Patented Wire", size_mm=s, size_label=f"{s:.2f} MM",
                         grade="HC72B", unit_of_measure="MTS",
                         display_name=f"HC Patented Wire {s:.2f}mm", hsn_code="722990", gst_pct=18.0))

    for s in [0.80, 0.90, 1.00, 1.25, 1.40, 1.60, 2.00]:
        rows.append(dict(product_type="GI Wire", size_mm=s, size_label=f"{s:.2f} MM IS",
                         grade="IS", unit_of_measure="MT",
                         display_name=f"GI Wire {s:.2f}mm IS", hsn_code="722990", gst_pct=18.0))

    for label, size, grade in [
        ("2F 4.5mm DIA FRP & Yarn", 4.5, "2F FRP Yarn"),
        ("4F UT UA 5.8mm FRP With Yarn", 5.8, "4F FRP Yarn"),
        ("6F UT UA 5.8mm FRP With Yarn", 5.8, "6F FRP Yarn"),
    ]:
        rows.append(dict(product_type="OFC Cable", size_mm=size, size_label=label,
                         grade=grade, unit_of_measure="KME",
                         display_name=f"OFC Cable {label}", hsn_code="90011000", gst_pct=18.0))

    upsert_batch("products", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 2. CUSTOMERS — from real ERP + CRM Excel
# ─────────────────────────────────────────────────────────────────────────────
def seed_customers():
    print("\n👥 Seeding customers...")
    # Calculate real order stats from invoices
    inv_stats = {}
    invoices = load_json("invoices.json")
    for i in invoices:
        name = str(i.get("cust_name", "")).strip()
        if not name: continue
        try: qty = float(str(i.get("prod_qty", "")).replace(",", "").strip())
        except: qty = 0.0
        if name not in inv_stats: inv_stats[name] = {"orders": 0, "qty": 0.0}
        inv_stats[name]["orders"] += 1
        inv_stats[name]["qty"] += qty

    rows = []
    seen = set()
    
    def add_customer(name, rep=None):
        if not name or name in seen: return
        seen.add(name)
        stats = inv_stats.get(name, {"orders": 0, "qty": 0.0})
        rows.append(dict(
            name=name,
            total_orders=stats["orders"],
            total_qty_mt=stats["qty"],
            dispatched_qty_mt=stats["qty"],
            is_repeat=stats["orders"] > 0,
            sales_rep=rep
        ))

    raw = load_json("customers.json")
    for c in raw:
        add_customer(str(c.get("name", "")).strip())

    enquiries = load_json("enquiries.json")
    for e in enquiries:
        add_customer(str(e.get("cust_name", "")).strip(), e.get("emp_name"))

    upsert_batch("customers", rows, on_conflict="name")


# ─────────────────────────────────────────────────────────────────────────────
# 3. ENQUIRIES — 1,145 real ERP records
# ─────────────────────────────────────────────────────────────────────────────
def seed_enquiries():
    print("\n📋 Seeding enquiries (1,145 real ERP records)...")
    raw = load_json("enquiries.json")
    rows = []
    for e in raw:
        # Parse date
        d = None
        try:
            raw_date = e.get("created_on_formatted", "")
            if raw_date:
                d = dateparser.parse(raw_date, dayfirst=True).date().isoformat()
        except Exception:
            pass

        # Parse quantity and rates
        def safe_float(val):
            try:
                return float(str(val).replace(",", "").strip()) if val else None
            except Exception:
                return None

        rows.append(dict(
            erp_id=e.get("enquiry_no"),
            enquiry_date=d,
            customer_name=str(e.get("cust_name", "")).strip() or None,
            product_desc=e.get("prod_specification") or e.get("prod_categ"),
            quantity=safe_float(e.get("order_qty")),
            unit=e.get("unit_code"),
            unit_rate_inr=safe_float(e.get("price_offered")),
            status=str(e.get("status", "")).strip() or None,
            sales_rep=e.get("emp_name"),
            remarks=e.get("remarks"),
            raw_data=e,  # Store full original row as JSONB
        ))

    upsert_batch("enquiries", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 4. RM PRICES — master + RMS specs
# ─────────────────────────────────────────────────────────────────────────────
def seed_rm_prices():
    print("\n💰 Seeding RM prices...")
    rows = [
        dict(vendor_name="Rashmi Metallurgical", rm_size_mm=5.5, rm_grade="IS 7887 G-4",
             rate_per_mt_inr=53000, effective_date=date(2026, 5, 1).isoformat()),
        dict(vendor_name="Shyam Metalics",       rm_size_mm=5.5, rm_grade="IS 7887 G-4",
             rate_per_mt_inr=52250, effective_date=date(2026, 5, 1).isoformat()),
        dict(vendor_name="SKS Ispat",             rm_size_mm=5.5, rm_grade="IS 7887 G-4",
             rate_per_mt_inr=52000, effective_date=date(2026, 5, 1).isoformat()),
        dict(vendor_name="TATA Steel",            rm_size_mm=5.5, rm_grade="HC72B",
             rate_per_mt_inr=67000, effective_date=date(2026, 5, 1).isoformat()),
        dict(vendor_name="JSW Steel",             rm_size_mm=5.5, rm_grade="CAQ G-1",
             rate_per_mt_inr=52500, effective_date=date(2026, 5, 1).isoformat()),
        dict(vendor_name="Jindal",                rm_size_mm=8.5, rm_grade="IS 7887 G-3",
             rate_per_mt_inr=53500, effective_date=date(2026, 5, 1).isoformat()),
    ]
    upsert_batch("rm_prices", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 5. MACHINES
# ─────────────────────────────────────────────────────────────────────────────
def seed_machines():
    print("\n⚙️  Seeding machines...")
    machines_raw = [
        ("Sayli", "MS1", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 72),
        ("Sayli", "MS2", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 68),
        ("Sayli", "MS3", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 81),
        ("Sayli", "MS4", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 75),
        ("Sayli", "MS5", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 65),
        ("Sayli", "MS6", "medium_drawing", "MS Wire", 2.0, 8.0, 18, 70),
        ("Sayli", "MS7", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 78),
        ("Sayli", "MS8", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 60),
        ("Sayli", "F1",  "fine_drawing",   "MS Wire", 0.9, 2.5, 8,  82),
        ("Sayli", "F2",  "fine_drawing",   "MS Wire", 0.9, 2.5, 8,  75),
        ("Sayli", "F3",  "fine_drawing",   "MS Wire", 0.9, 2.5, 8,  88),
        ("Sayli", "F4",  "fine_drawing",   "MS Wire", 0.9, 2.5, 8,  71),
        ("Sayli", "F5",  "fine_drawing",   "MS Wire", 0.9, 2.5, 8,  66),
        ("Sayli", "F6",  "fine_drawing",   "MS Wire", 0.9, 2.5, 8,  79),
        ("Sayli", "F7",  "fine_drawing",   "MS Wire", 0.9, 2.5, 8,  84),
        ("Sayli", "F8",  "fine_drawing",   "MS Wire", 0.9, 2.5, 8,  73),
        ("Sayli", "WRC1","wire_rod_coiler","MS Wire", 5.5, 5.5, 20, 85),
        ("Sayli", "WRC2","wire_rod_coiler","MS Wire", 5.5, 5.5, 20, 78),
        ("Sayli", "WRC3","wire_rod_coiler","MS Wire", 5.5, 5.5, 20, 82),
        ("Veritas Unit 1","U1-HC-8B1",  "hc_drawing", "HC Patented Wire", 0.3, 6.0, 12, 74),
        ("Veritas Unit 1","U1-HC-7B1",  "hc_drawing", "HC Patented Wire", 0.3, 6.0, 12, 68),
        ("Veritas Unit 1","U1-HC-11B1", "hc_drawing", "HC Patented Wire", 0.3, 6.0, 12, 81),
        ("Veritas Unit 1","U1-HC-6B1",  "hc_drawing", "HC Patented Wire", 0.3, 6.0, 12, 72),
        ("Veritas Unit 2","U2-GI-L1",   "galvanising","GI Wire", 0.8, 2.0, 10, 76),
        ("Veritas Unit 2","U2-GI-L2",   "galvanising","GI Wire", 0.8, 2.0, 10, 70),
        ("Veritas Unit 2","U2-GI-L3",   "galvanising","GI Wire", 0.8, 2.0, 10, 82),
        ("Veritas Unit 3","U3-GS-L1",   "galvanising","GI Wire", 2.0, 4.0, 14, 65),
        ("Veritas Unit 3","U3-GS-L2",   "galvanising","GI Wire", 2.0, 4.0, 14, 72),
        ("Veritas Unit 4","U4-FCA-1",   "galvanising","GI Wire", 0.8, 3.0, 12, 77),
        ("Veritas Unit 4","U4-RCA-1",   "galvanising","GI Wire", 2.0, 4.0, 12, 69),
    ]
    rows = [dict(unit_name=u, machine_code=c, machine_type=mt, product_types=pt,
                 min_dia_mm=mn, max_dia_mm=mx, capacity_mt_per_day=cap,
                 current_utilisation_pct=util, active=True)
            for u, c, mt, pt, mn, mx, cap, util in machines_raw]
    upsert_batch("machines", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 6. FG INVENTORY
# ─────────────────────────────────────────────────────────────────────────────
def seed_fg_inventory():
    print("\n📊 Seeding FG inventory...")
    today = date.today().isoformat()
    fg_data = [
        ("Sayli", "MS Wire", "1.38 MM", 8.5),
        ("Sayli", "MS Wire", "1.58 MM", 12.3),
        ("Sayli", "MS Wire", "2.12 MM", 6.7),
        ("Sayli", "MS Wire", "2.49 MM", 15.2),
        ("Sayli", "MS Wire", "2.62 MM", 22.4),
        ("Sayli", "MS Wire", "2.98 MM", 9.1),
        ("Sayli", "MS Wire", "3.13 MM", 11.8),
        ("Sayli", "MS Wire", "5.58 MM", 18.6),
        ("Veritas Unit 1", "HC Patented Wire", "5.10 MM", 14.2),
        ("Veritas Unit 1", "HC Patented Wire", "5.68 MM", 8.7),
        ("Veritas Unit 1", "HC Patented Wire", "4.90 MM", 6.3),
        ("Veritas Unit 2", "GI Wire", "0.80 MM IS", 7.2),
        ("Veritas Unit 2", "GI Wire", "0.90 MM IS", 34.5),
        ("Veritas Unit 2", "GI Wire", "1.00 MM IS", 5.8),
        ("Veritas Unit 2", "GI Wire", "1.25 MM IS", 28.7),
        ("Veritas Unit 2", "GI Wire", "1.40 MM IS", 12.1),
        ("Veritas Unit 2", "GI Wire", "1.60 MM IS", 8.9),
        ("Veritas Unit 3", "GI Wire", "2.00 MM IS", 15.3),
        ("Veritas Unit 4", "GI Wire", "2.00 MM IS", 8.5),
        ("Veritas Unit 1", "OFC Cable", "2F 4.5mm DIA FRP & Yarn", 2.5),
        ("Veritas Unit 1", "OFC Cable", "4F UT UA 5.8mm FRP With Yarn", 1.8),
        ("Veritas Unit 1", "OFC Cable", "6F UT UA 5.8mm FRP With Yarn", 0.9),
    ]
    rows = [dict(snapshot_date=today, unit_name=u, product_type=pt,
                 size_label=sl, quantity_mt=q, inventory_type="FG")
            for u, pt, sl, q in fg_data]
    upsert_batch("fg_inventory", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 7. QUOTE HISTORY — derived from real enquiries
# ─────────────────────────────────────────────────────────────────────────────
def seed_quote_history():
    print("\n📜 Seeding quote history from real enquiries...")
    enquiries = load_json("enquiries.json")
    rows = []

    product_map = {
        "GI": "GI Wire",
        "MS": "MS Wire",
        "HC": "HC Patented Wire",
        "OFC": "OFC Cable",
        "ACSR": "HC Patented Wire",
        "ACS": "HC Patented Wire",
    }

    for e in enquiries:
        try:
            # Map product type
            categ = str(e.get("prod_categ", "")).upper()
            ptype = "MS Wire"
            for key, val in product_map.items():
                if key in categ:
                    ptype = val
                    break

            # Parse date
            d = None
            try:
                raw_d = e.get("created_on_formatted", "")
                if raw_d:
                    d = dateparser.parse(raw_d, dayfirst=True).date().isoformat()
            except Exception:
                d = date.today().isoformat()

            # Parse rate and qty
            def sf(v):
                try:
                    return float(str(v).replace(",", "").strip()) if v else None
                except Exception:
                    return None

            rate = sf(e.get("price_offered")) or sf(e.get("target_price"))
            qty  = sf(e.get("order_qty")) or 1.0

            if not rate or rate <= 0:
                continue  # Skip enquiries with no price data

            status = str(e.get("status", "")).strip().upper()
            if "WIN" in status or "ORDER" in status or "CONFIRM" in status:
                outcome = "won"
            elif "LOST" in status or "CANCEL" in status or "REJECT" in status:
                outcome = "lost"
            else:
                outcome = "pending"

            spec = e.get("prod_specification") or e.get("prod_categ") or ""

            rows.append(dict(
                quote_date=d,
                customer_name=str(e.get("cust_name", "")).strip() or "Unknown",
                product_type=ptype,
                size_label=spec[:100],
                grade=None,
                quantity=qty,
                unit=e.get("unit_code") or "MT",
                unit_rate_inr=rate,
                net_amount_inr=round(rate * qty, 2),
                payment_terms=None,
                credit_days=None,
                outcome=outcome,
                sales_rep=e.get("emp_name"),
                notes=e.get("remarks"),
            ))
        except Exception as ex:
            continue  # Skip malformed rows

    upsert_batch("quote_history", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 8. SEED TODAY'S DAILY RATES (default)
# ─────────────────────────────────────────────────────────────────────────────
def seed_daily_rates():
    print("\n📈 Seeding today's default daily rates...")
    rows = [dict(
        rate_date=date.today().isoformat(),
        ms_steel_rate=52000.0,
        hc_steel_rate=67000.0,
        zinc_rate=260.0,
        entered_by="System Default",
    )]
    upsert_batch("daily_rates", rows)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Quote Intelligence — Supabase ETL Loader")
    print(f"   Project: {SUPABASE_URL}")
    print("=" * 60)

    seed_products()
    seed_customers()
    seed_rm_prices()
    seed_machines()
    seed_fg_inventory()
    seed_enquiries()
    seed_quote_history()
    seed_daily_rates()

    print("\n" + "=" * 60)
    print("✅ All data loaded into Supabase successfully!")
    print("=" * 60)
