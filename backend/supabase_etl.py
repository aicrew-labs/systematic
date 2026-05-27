from __future__ import annotations
"""
Supabase ETL Loader — Quote Intelligence v2
============================================
Loads all ERP data into Supabase with proper FK relationships.

Table load order (respects FK dependencies):
  1. products          (no FK deps)
  2. customers         (no FK deps)
  3. manufacturing_units (no FK deps)
  4. enquiries         (FK → customers, products)
  5. sales_orders      (FK → customers, products, manufacturing_units)
  6. invoices          (FK → customers, products, manufacturing_units)
  7. fg_inventory      (FK → products, manufacturing_units)
  8. machines          (FK → manufacturing_units)
  9. rm_prices         (standalone)
  10. daily_rates      (standalone)

Usage:
    python3 backend/supabase_etl.py
"""

import json, os, re, sys
from datetime import date, datetime
from dateutil import parser as dateparser
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("ERROR: SUPABASE_URL and SUPABASE_KEY must be set (see .env.example).")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "erp_data")
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

from supabase import create_client, Client
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Helpers ─────────────────────────────────────────────────────────────────

def load_json(filename: str) -> list:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  ⚠️  {filename} not found, skipping.")
        return []
    with open(path) as f:
        return json.load(f)

def safe_float(val) -> float | None:
    try:
        return float(str(val).replace(",", "").strip()) if val else None
    except Exception:
        return None

def safe_int(val) -> int | None:
    try:
        return int(str(val).strip()) if val else None
    except Exception:
        return None

def parse_date(val: str) -> str | None:
    if not val:
        return None
    try:
        return dateparser.parse(val, dayfirst=True).date().isoformat()
    except Exception:
        return None

# ── Product resolver ────────────────────────────────────────────────────────
# Normalizes free-text product strings (e.g. "HC Patented Wire 5.68 MM",
# "GI Wire 2.62 MM", "OFC 6F UT UA 5.8mm FRP With Yarn") into a
# (canonical_type, size_mm) tuple, then matches against products.id.
#
# Returns a dict callable: resolve(prod_text) -> int | None

import re

# Canonical type keywords ordered most-specific first.
# When scanning a text, the first matching keyword wins.
_TYPE_KEYWORDS = [
    ("HC Patented Wire", ["HC PATENTED", "HCP "]),
    ("HC",               ["HC WIRE", " HC ", "HC72"]),
    ("OFC Cable",        ["OFC ", " OFC", "FRP", "ADSS"]),
    ("OPGW",             ["OPGW"]),
    ("GI Strip (FCA)",   ["GI STRIP (FCA)", "FCA "]),
    ("GI Strip",         ["GI STRIP", "STRIP"]),
    ("GI WIRE / GALVASYS", ["GALVASYS", "GI WIRE", "GI ", "G.I.", "RCA"]),
    ("ACSR (HTGS)",      ["ACSR (HTGS)", "HTGS", "ACSR"]),
    ("ACS",              ["ACS "]),
    ("MS Wire",          ["MS WIRE", " MS ", "ANNEALED"]),
    ("Stranded Wire",    ["STRANDED", "STRAND"]),
    ("Weldmesh",         ["WELDMESH", "WELD MESH"]),
    ("Barbed",           ["BARBED"]),
    ("Chain Link",       ["CHAIN LINK", "CHAINLINK"]),
]

def _canon_type(text: str) -> str | None:
    if not text:
        return None
    upper = text.upper()
    for canon, keys in _TYPE_KEYWORDS:
        if any(k in upper for k in keys):
            return canon
    return None

def _extract_size_mm(text: str) -> float | None:
    """Pull the first plausible diameter (1.0–20.0 mm) from a free-text string."""
    if not text:
        return None
    # Look for explicit MM markers first
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:mm|MM)", text)
    if m:
        v = safe_float(m.group(1))
        if v and 0.3 <= v <= 20.0:
            return v
    # Fallback: any decimal number in plausible wire-diameter range
    for tok in re.findall(r"\d+(?:\.\d+)?", text):
        v = safe_float(tok)
        if v and 0.3 <= v <= 20.0:
            return v
    return None

def build_product_resolver() -> callable:
    """
    Loads products into memory and returns a resolver(text) -> product_id|None.
    Match strategy: canonical_type match (loose) + size within ±0.05 mm.
    """
    res = sb.table("products").select("id, product_type, size_mm, size_label").limit(10000).execute()
    products = res.data or []
    # Bucket by canonical type
    buckets: dict[str, list] = {}
    for p in products:
        canon = _canon_type(p.get("product_type") or "") or _canon_type(p.get("size_label") or "")
        if canon:
            buckets.setdefault(canon, []).append(p)

    print(f"  Product resolver: {len(products)} products bucketed into {len(buckets)} canonical types")

    unmatched: list[str] = []

    def resolve(text: str) -> int | None:
        if not text:
            return None
        canon = _canon_type(text)
        size  = _extract_size_mm(text)
        if not canon or size is None:
            unmatched.append(text)
            return None
        candidates = buckets.get(canon, [])
        # Best size match within ±0.05 mm tolerance
        best = None
        best_diff = 0.06
        for p in candidates:
            psize = p.get("size_mm")
            if psize is None:
                continue
            d = abs(psize - size)
            if d < best_diff:
                best = p
                best_diff = d
        if best:
            return best["id"]
        unmatched.append(text)
        return None

    resolve.unmatched = unmatched  # type: ignore[attr-defined]
    return resolve


def _trim(s, n: int = 500):
    """Truncate strings defensively so wide ERP free-text fields don't overflow."""
    if s is None:
        return None
    s = str(s)
    return s if len(s) <= n else s[:n]


def upsert_batch(table: str, rows: list, batch_size: int = 200, on_conflict: str = None):
    if not rows:
        print(f"  ⚠️  No rows to insert for {table}")
        return 0
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            if on_conflict:
                sb.table(table).upsert(batch, on_conflict=on_conflict).execute()
            else:
                sb.table(table).upsert(batch).execute()
            total += len(batch)
            print(f"  → {table}: {total}/{len(rows)} rows", end="\r")
        except Exception as e:
            print(f"\n  ❌ Error upserting {table} batch {i}: {e}")
    print(f"  ✅ {table}: {total} rows loaded.           ")
    return total

def clear_table(table: str):
    try:
        sb.table(table).delete().neq("id", -9999).execute()
        print(f"  🧹 Cleared {table}")
    except Exception as e:
        print(f"  ⚠️  Could not clear {table}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. PRODUCTS — from ERP RMS module
# ─────────────────────────────────────────────────────────────────────────────
def seed_products():
    print("\n📦 Seeding products from rms_specs.json...")
    raw = load_json("rms_specs.json")
    rows = []
    seen = set()

    for item in raw:
        try:
            oid = int(item.get("order_id", 0))
        except (ValueError, TypeError):
            continue
        if not oid or oid in seen:
            continue
        seen.add(oid)

        product_type = (item.get("product_type") or "Other").strip() or "Other"
        size_label   = (item.get("order_no") or "").strip()
        if not size_label:
            continue

        # Parse diameter
        size_mm = None
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:mm|MM)", size_label)
        if m:
            size_mm = safe_float(m.group(1))
        elif re.search(r"(\d+(?:\.\d+)?)", size_label):
            size_mm = safe_float(re.search(r"(\d+(?:\.\d+)?)", size_label).group(1))

        pt_upper = product_type.upper()
        uom = "KME" if any(k in pt_upper for k in ["OFC","CABLE","OPGW"]) else \
              "MTS" if "HC" in pt_upper else "MT"
        hsn  = "90011000" if any(k in pt_upper for k in ["OFC","CABLE"]) else "722990"
        grade = "IS" if "IS" in size_label.upper() else \
                "HC" if "HC" in pt_upper or "HC" in size_label.upper() else "Standard"

        rows.append({
            "id":              oid,
            "product_type":    product_type,
            "size_mm":         size_mm,
            "size_label":      size_label,
            "grade":           grade,
            "unit_of_measure": uom,
            "display_name":    f"{product_type} - {size_label}",
            "hsn_code":        hsn,
            "gst_pct":         18.0,
            "is_active":       item.get("isactive", "Yes") == "Yes",
        })

    upsert_batch("products", rows, on_conflict="id")


# ─────────────────────────────────────────────────────────────────────────────
# 2. CUSTOMERS — from ERP customers_full.json (1,306 customers)
# ─────────────────────────────────────────────────────────────────────────────
def seed_customers():
    print("\n👥 Seeding customers from customers_full.json...")

    # Build invoice stats (orders & qty per customer name)
    inv_stats: dict[str, dict] = {}
    for inv in load_json("invoices.json"):
        name = str(inv.get("cust_name", "")).strip()
        if not name:
            continue
        qty = safe_float(inv.get("prod_qty")) or 0.0
        if name not in inv_stats:
            inv_stats[name] = {"orders": 0, "qty": 0.0, "rep": None}
        inv_stats[name]["orders"] += 1
        inv_stats[name]["qty"]    += qty
        if not inv_stats[name]["rep"]:
            inv_stats[name]["rep"] = inv.get("emp_name")

    # Load from full customer file (1,306 rows)
    raw = load_json("customers_full.json")
    if not raw:
        print("  ⚠️  customers_full.json empty, falling back to customers.json")
        raw = load_json("customers.json")

    rows = []
    seen_ids   = set()
    seen_names = set()

    for c in raw:
        cid_str = str(c.get("customer_id", "")).strip()
        name    = str(c.get("name", "")).strip()
        if not cid_str or not cid_str.isdigit() or not name:
            continue
        cid = int(cid_str)
        if cid in seen_ids or name in seen_names:
            continue
        seen_ids.add(cid)
        seen_names.add(name)

        stats = inv_stats.get(name, {"orders": 0, "qty": 0.0, "rep": None})
        rows.append({
            "id":                cid,
            "name":              name,
            "phone":             c.get("phone"),
            "company_id":        safe_int(c.get("company_id")),
            "total_orders":      stats["orders"],
            "total_qty_mt":      stats["qty"],
            "dispatched_qty_mt": stats["qty"],
            "is_repeat":         stats["orders"] > 0,
            "sales_rep":         stats["rep"],
        })

    print(f"  Loaded {len(rows)} customers with ERP customer_id as PK")
    upsert_batch("customers", rows, on_conflict="id")

    return seen_names  # Return for use by later ETL steps


# ─────────────────────────────────────────────────────────────────────────────
# 3. MANUFACTURING UNITS — internal master
# ─────────────────────────────────────────────────────────────────────────────
MFG_UNITS = [
    {"name": "Sayli",          "billing_code": "SIL",   "location": "Sayli, Silvassa"},
    {"name": "Veritas Unit 1", "billing_code": "VIPL",  "location": "Sarigam, Gujarat"},
    {"name": "Veritas Unit 2", "billing_code": "VIPL",  "location": "Sarigam, Gujarat"},
    {"name": "Veritas Unit 3", "billing_code": "SIGM",  "location": "Sarigam, Gujarat"},
    {"name": "Veritas Unit 4", "billing_code": "WBIPL", "location": "Sarigam, Gujarat"},
    {"name": "Naroli",         "billing_code": "SIL",   "location": "Naroli, Silvassa"},
    {"name": "Umerqui",        "billing_code": "SIL",   "location": "Umerqui, Silvassa"},
    {"name": "Vadodara",       "billing_code": "SIGM",  "location": "Vadodara, Gujarat"},
]

def seed_manufacturing_units() -> dict[str, int]:
    """Seed and return a name→id lookup."""
    print("\n🏭 Seeding manufacturing_units...")
    upsert_batch("manufacturing_units", MFG_UNITS, on_conflict="name")

    # Fetch back to get serial IDs
    res = sb.table("manufacturing_units").select("id, name").execute()
    unit_map = {r["name"]: r["id"] for r in (res.data or [])}
    print(f"  Unit map: {unit_map}")
    return unit_map


def resolve_unit_id(unit_name: str, unit_map: dict) -> int | None:
    """Match a free-text unit name to manufacturing_units.id."""
    if not unit_name:
        return None
    for name, uid in unit_map.items():
        if name.lower() in unit_name.lower() or unit_name.lower() in name.lower():
            return uid
    # Billing code lookup
    billing_map = {"SIL": "Sayli", "VIPL": "Veritas Unit 1",
                   "SIGM": "Veritas Unit 3", "WBIPL": "Veritas Unit 4"}
    for code, uname in billing_map.items():
        if code in unit_name.upper():
            return unit_map.get(uname)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. ENQUIRIES — from ERP CRM (one row per line item)
# ─────────────────────────────────────────────────────────────────────────────
def seed_enquiries(customer_map: dict[str, int], resolve_product):
    """customer_map: name → customer_id for FK resolution."""
    print("\n📋 Seeding enquiries (one row per line item)...")
    raw = load_json("enquiries.json")
    rows = []

    for e in raw:
        try:
            cust_name = str(e.get("cust_name", "")).strip()
            prod_text = e.get("prod_specification") or e.get("prod_categ") or ""
            rows.append({
                "erp_id":        e.get("enquiry_no"),
                "enquiry_date":  parse_date(e.get("created_on_formatted")),
                "customer_id":   customer_map.get(cust_name),   # FK — null if not in ERP
                "customer_name": cust_name or None,
                "product_id":    resolve_product(prod_text),    # fuzzy match → products.id
                "product_desc":  e.get("prod_specification"),
                "prod_category": e.get("prod_categ"),
                "quantity":      safe_float(e.get("order_qty")),
                "unit":          e.get("unit_code"),
                "price_offered": safe_float(e.get("price_offered")),
                "target_price":  safe_float(e.get("target_price")),
                "status":        str(e.get("status", "")).strip() or None,
                "sales_rep":     e.get("emp_name"),
                "source":        e.get("enquiry_source"),
                "cust_type":     e.get("cust_type"),
                "remarks":       e.get("remarks"),
                "raw_data":      e,
            })
        except Exception as ex:
            continue

    upsert_batch("enquiries", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 5. SALES ORDERS — from pending_orders.json
# ─────────────────────────────────────────────────────────────────────────────
def seed_sales_orders(customer_map: dict[str, int], unit_map: dict[str, int], resolve_product):
    print("\n📦 Seeding sales_orders from pending_orders.json...")
    raw = load_json("pending_orders.json")
    rows = []

    for o in raw:
        try:
            cust_name = str(o.get("cust_name", "")).strip()
            billing   = str(o.get("billing_unit", "")).strip()
            prod_text = o.get("prod_code") or o.get("prod_categ") or ""
            rows.append({
                "erp_so_no":       o.get("order_no"),
                "erp_do_no":       None,
                "erp_enquiry_id":  None,                       # Not in pending_orders data
                "order_date":      parse_date(o.get("order_date")),
                "customer_id":     customer_map.get(cust_name),
                "customer_name":   cust_name or None,
                "product_id":      resolve_product(prod_text), # fuzzy match → products.id
                "prod_code":       o.get("prod_code"),
                "quantity":        safe_float(o.get("prod_qty")),
                "pending_qty":     safe_float(o.get("pending_qty")),
                "dispatched_qty":  safe_float(o.get("dispatch_qty")),
                "unit":            None,
                "unit_rate":       safe_float(o.get("unit_rate")),
                "freight":         o.get("freight"),
                "payment_terms":   _trim(o.get("payment_term"), 500),
                "credit_days":     None,
                "billing_unit_id": resolve_unit_id(billing, unit_map),
                "dispatch_from":   _trim(o.get("dispatch_from"), 500),
                "po_number":       o.get("po_number"),
                "status":          o.get("order_status"),
                "sales_rep":       o.get("emp_name"),
            })
        except Exception as ex:
            continue

    upsert_batch("sales_orders", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 6. INVOICES — from invoices.json
# ─────────────────────────────────────────────────────────────────────────────
def seed_invoices(customer_map: dict[str, int], unit_map: dict[str, int], resolve_product):
    print("\n🧾 Seeding invoices from invoices.json...")
    raw = load_json("invoices.json")
    rows = []

    for inv in raw:
        try:
            cust_name = str(inv.get("cust_name", "")).strip()
            billing   = str(inv.get("billing_unit", "")).strip()
            prod_text = inv.get("prod_code") or ""

            # Parse credit_days from payment_terms string e.g. "30-Days" → 30
            credit = safe_int(inv.get("credit_days")) or 0

            rows.append({
                "erp_invoice_id":  inv.get("invoice_id"),
                "erp_inv_nos":     inv.get("inv_nos"),
                "erp_so_no":       inv.get("so_number"),
                "erp_do_no":       inv.get("do_number"),
                "invoice_date":    parse_date(inv.get("order_date")),
                "due_date":        parse_date(inv.get("due_date")),
                "customer_id":     customer_map.get(cust_name),
                "customer_name":   cust_name or None,
                "product_id":      resolve_product(prod_text), # fuzzy match → products.id
                "prod_code":       inv.get("prod_code"),
                "quantity":        safe_float(inv.get("prod_qty")),
                "unit":            inv.get("uom"),
                "unit_rate":       safe_float(inv.get("unit_rate")),
                "freight":         inv.get("freight"),
                "payment_terms":   _trim(inv.get("payment_terms"), 500),
                "credit_days":     credit,
                "billing_unit_id": resolve_unit_id(billing, unit_map),
                "dispatch_from":   _trim(str(inv.get("dispatch_from", "")).strip() or None, 500),
                "po_number":       inv.get("po_number"),
                "po_date":         parse_date(inv.get("po_date")),
                "order_status":    inv.get("order_status"),
                "voucher_type":    inv.get("voucher_type"),
                "cgst":            safe_float(inv.get("cgst")),
                "sgst":            safe_float(inv.get("sgst")),
                "igst":            safe_float(str(inv.get("igst", "0")).strip() or "0"),
                "prod_total":      safe_float(inv.get("prod_total")),
                "total_amount":    safe_float(inv.get("totalamt")),
                "sales_rep":       inv.get("emp_name"),
                "outcome":         "won",
            })
        except Exception as ex:
            continue

    upsert_batch("invoices", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 7. FG INVENTORY
# ─────────────────────────────────────────────────────────────────────────────
def seed_fg_inventory(unit_map: dict[str, int]):
    print("\n📊 Seeding fg_inventory...")
    today = date.today().isoformat()

    # Lookup products by size_label for FK
    prod_res = sb.table("products").select("id, size_label").limit(10000).execute()
    prod_map = {r["size_label"].strip().lower(): r["id"] for r in (prod_res.data or [])}

    fg_data = [
        ("Sayli",          "MS Wire",          "1.38 MM",                        8.5),
        ("Sayli",          "MS Wire",          "1.58 MM",                        12.3),
        ("Sayli",          "MS Wire",          "2.12 MM",                        6.7),
        ("Sayli",          "MS Wire",          "2.49 MM",                        15.2),
        ("Sayli",          "MS Wire",          "2.62 MM",                        22.4),
        ("Sayli",          "MS Wire",          "2.98 MM",                        9.1),
        ("Sayli",          "MS Wire",          "3.13 MM",                        11.8),
        ("Sayli",          "MS Wire",          "5.58 MM",                        18.6),
        ("Veritas Unit 1", "HC Patented Wire", "5.10 MM",                        14.2),
        ("Veritas Unit 1", "HC Patented Wire", "5.68 MM",                        8.7),
        ("Veritas Unit 1", "HC Patented Wire", "4.90 MM",                        6.3),
        ("Veritas Unit 2", "GI Wire",          "0.80 MM IS",                     7.2),
        ("Veritas Unit 2", "GI Wire",          "0.90 MM IS",                     34.5),
        ("Veritas Unit 2", "GI Wire",          "1.00 MM IS",                     5.8),
        ("Veritas Unit 2", "GI Wire",          "1.25 MM IS",                     28.7),
        ("Veritas Unit 2", "GI Wire",          "1.40 MM IS",                     12.1),
        ("Veritas Unit 2", "GI Wire",          "1.60 MM IS",                     8.9),
        ("Veritas Unit 3", "GI Wire",          "2.00 MM IS",                     15.3),
        ("Veritas Unit 4", "GI Wire",          "2.00 MM IS",                     8.5),
        ("Veritas Unit 1", "OFC Cable",        "2F 4.5mm DIA FRP & Yarn",        2.5),
        ("Veritas Unit 1", "OFC Cable",        "4F UT UA 5.8mm FRP With Yarn",   1.8),
        ("Veritas Unit 1", "OFC Cable",        "6F UT UA 5.8mm FRP With Yarn",   0.9),
    ]

    rows = []
    for unit_name, ptype, slabel, qty in fg_data:
        rows.append({
            "snapshot_date":  today,
            "unit_id":        unit_map.get(unit_name),
            "unit_name":      unit_name,
            "product_id":     prod_map.get(slabel.strip().lower()),
            "product_type":   ptype,
            "size_label":     slabel,
            "quantity_mt":    qty,
            "inventory_type": "FG",
        })

    upsert_batch("fg_inventory", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 8. MACHINES
# ─────────────────────────────────────────────────────────────────────────────
def seed_machines(unit_map: dict[str, int]):
    print("\n⚙️  Seeding machines...")
    machines_raw = [
        ("Sayli",          "MS1",      "medium_drawing",  2.0, 6.0, 18, 72),
        ("Sayli",          "MS2",      "medium_drawing",  2.0, 6.0, 18, 68),
        ("Sayli",          "MS3",      "medium_drawing",  2.0, 6.0, 18, 81),
        ("Sayli",          "MS4",      "medium_drawing",  2.0, 6.0, 18, 75),
        ("Sayli",          "MS5",      "medium_drawing",  2.0, 6.0, 18, 65),
        ("Sayli",          "MS6",      "medium_drawing",  2.0, 8.0, 18, 70),
        ("Sayli",          "MS7",      "medium_drawing",  2.0, 6.0, 18, 78),
        ("Sayli",          "MS8",      "medium_drawing",  2.0, 6.0, 18, 60),
        ("Sayli",          "F1",       "fine_drawing",    0.9, 2.5,  8, 82),
        ("Sayli",          "F2",       "fine_drawing",    0.9, 2.5,  8, 75),
        ("Sayli",          "F3",       "fine_drawing",    0.9, 2.5,  8, 88),
        ("Sayli",          "F4",       "fine_drawing",    0.9, 2.5,  8, 71),
        ("Sayli",          "F5",       "fine_drawing",    0.9, 2.5,  8, 66),
        ("Sayli",          "F6",       "fine_drawing",    0.9, 2.5,  8, 79),
        ("Sayli",          "F7",       "fine_drawing",    0.9, 2.5,  8, 84),
        ("Sayli",          "F8",       "fine_drawing",    0.9, 2.5,  8, 73),
        ("Sayli",          "WRC1",     "wire_rod_coiler", 5.5, 5.5, 20, 85),
        ("Sayli",          "WRC2",     "wire_rod_coiler", 5.5, 5.5, 20, 78),
        ("Sayli",          "WRC3",     "wire_rod_coiler", 5.5, 5.5, 20, 82),
        ("Veritas Unit 1", "U1-HC-8B1",  "hc_drawing",   0.3, 6.0, 12, 74),
        ("Veritas Unit 1", "U1-HC-7B1",  "hc_drawing",   0.3, 6.0, 12, 68),
        ("Veritas Unit 1", "U1-HC-11B1", "hc_drawing",   0.3, 6.0, 12, 81),
        ("Veritas Unit 1", "U1-HC-6B1",  "hc_drawing",   0.3, 6.0, 12, 72),
        ("Veritas Unit 2", "U2-GI-L1",  "galvanising",   0.8, 2.0, 10, 76),
        ("Veritas Unit 2", "U2-GI-L2",  "galvanising",   0.8, 2.0, 10, 70),
        ("Veritas Unit 2", "U2-GI-L3",  "galvanising",   0.8, 2.0, 10, 82),
        ("Veritas Unit 3", "U3-GS-L1",  "galvanising",   2.0, 4.0, 14, 65),
        ("Veritas Unit 3", "U3-GS-L2",  "galvanising",   2.0, 4.0, 14, 72),
        ("Veritas Unit 4", "U4-FCA-1",  "galvanising",   0.8, 3.0, 12, 77),
        ("Veritas Unit 4", "U4-RCA-1",  "galvanising",   2.0, 4.0, 12, 69),
    ]
    rows = [{
        "unit_id":                  unit_map.get(unit),
        "unit_name":                unit,
        "machine_code":             code,
        "machine_type":             mtype,
        "min_dia_mm":               mn,
        "max_dia_mm":               mx,
        "capacity_mt_per_day":      cap,
        "current_utilisation_pct":  util,
        "active":                   True,
    } for unit, code, mtype, mn, mx, cap, util in machines_raw]
    upsert_batch("machines", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 9. RM PRICES
# ─────────────────────────────────────────────────────────────────────────────
def seed_rm_prices():
    print("\n💰 Seeding rm_prices...")
    rows = [
        {"vendor_name": "Rashmi Metallurgical", "rm_size_mm": 5.5, "rm_grade": "IS 7887 G-4", "rate_per_mt_inr": 53000, "effective_date": "2026-05-01"},
        {"vendor_name": "Shyam Metalics",       "rm_size_mm": 5.5, "rm_grade": "IS 7887 G-4", "rate_per_mt_inr": 52250, "effective_date": "2026-05-01"},
        {"vendor_name": "SKS Ispat",             "rm_size_mm": 5.5, "rm_grade": "IS 7887 G-4", "rate_per_mt_inr": 52000, "effective_date": "2026-05-01"},
        {"vendor_name": "TATA Steel",            "rm_size_mm": 5.5, "rm_grade": "HC72B",       "rate_per_mt_inr": 67000, "effective_date": "2026-05-01"},
        {"vendor_name": "JSW Steel",             "rm_size_mm": 5.5, "rm_grade": "CAQ G-1",     "rate_per_mt_inr": 52500, "effective_date": "2026-05-01"},
        {"vendor_name": "Jindal",                "rm_size_mm": 8.5, "rm_grade": "IS 7887 G-3", "rate_per_mt_inr": 53500, "effective_date": "2026-05-01"},
    ]
    upsert_batch("rm_prices", rows)


# ─────────────────────────────────────────────────────────────────────────────
# 10. DAILY RATES
# ─────────────────────────────────────────────────────────────────────────────
def seed_daily_rates():
    print("\n📈 Seeding daily_rates...")
    rows = [{
        "rate_date": date.today().isoformat(),
        "prime_steel_rate": 52000.0,
        "hc_steel_rate": 67000.0,
        "commercial_steel_rate": 50000.0,
        "zinc_sgh_rate": 260.0,
        "zinc_rate": 260.0,
        "wire_rod_rate": 50000.0,
        "conv_wiping_fine_rate": 10000.0,
        "conv_wiping_thick_rate": 8000.0,
        "conv_heavy_fine_rate": 12000.0,
        "conv_heavy_thick_rate": 10000.0,
        "conv_printing_rate": 2000.0,
        "conv_stranding_rate": 3000.0,
        "entered_by": "System Default"
    }]
    upsert_batch("daily_rates", rows)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("🚀 Quote Intelligence — Supabase ETL Loader v2")
    print(f"   Project: {SUPABASE_URL}")
    print("=" * 65)

    # Clear all tables in reverse FK order
    print("\n🧹 Clearing tables...")
    for t in ["fg_inventory","machines","invoices","sales_orders","enquiries",
              "manufacturing_units","customers","products","rm_prices","daily_rates"]:
        clear_table(t)

    # Load in FK dependency order
    seed_products()
    customer_names = seed_customers()

    # Build customer name→id map for FK resolution
    print("\n  Building customer name→id lookup...")
    res = sb.table("customers").select("id, name").limit(10000).execute()
    customer_map = {r["name"]: r["id"] for r in (res.data or [])}
    print(f"  {len(customer_map)} customers in map")

    unit_map = seed_manufacturing_units()

    # Build product resolver (fuzzy text → products.id)
    print("\n🔍 Building product resolver...")
    resolve_product = build_product_resolver()

    seed_enquiries(customer_map, resolve_product)
    seed_sales_orders(customer_map, unit_map, resolve_product)
    seed_invoices(customer_map, unit_map, resolve_product)
    seed_fg_inventory(unit_map)
    seed_machines(unit_map)
    seed_rm_prices()
    seed_daily_rates()

    # Report unmatched products
    n_unmatched = len(resolve_product.unmatched)
    if n_unmatched:
        print(f"\n⚠️  {n_unmatched} rows could not be matched to a product")
        print(f"   Sample (first 5): {resolve_product.unmatched[:5]}")

    # Final counts
    print("\n" + "=" * 65)
    print("✅ ETL Complete — Final row counts:")
    for t in ["products","customers","manufacturing_units","enquiries",
              "sales_orders","invoices","fg_inventory","machines","rm_prices","daily_rates"]:
        try:
            res = sb.table(t).select("id", count="exact").limit(1).execute()
            print(f"   {t:25s}: {res.count:>6,} rows")
        except Exception as e:
            print(f"   {t:25s}: error — {e}")
    print("=" * 65)
