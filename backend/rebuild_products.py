"""
One-shot rebuild of the products catalog.

Strategy:
  1. Mine all unique product strings from invoices.prod_code,
     sales_orders.prod_code, enquiries.prod_specification.
  2. Normalize each to (canonical_type, size_label, size_mm).
  3. Insert one row per unique (canonical_type, size_label) into products.
  4. Build a resolver and re-link every transactional row by product_id.
  5. Populate product_rms_specs from rms_specs.json as enrichment.

Run:
    SBP_TOKEN=... python3 backend/rebuild_products.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("ERROR: SUPABASE_URL and SUPABASE_KEY must be set (see .env.example).")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "erp_data")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Canonical product types ─────────────────────────────────────────────────

# Order matters: most-specific keywords first.
TYPE_RULES = [
    ("HC Patented Wire", ["HC PATENTED", "HCP "]),
    ("OFC Cable",        ["OFC ", "ADSS", " FRP"]),
    ("OPGW",             ["OPGW"]),
    ("PC Wire",          ["PC WIRE", "PC-WIRE"]),
    ("GI Strip",         ["GI STRIP", "STRIP"]),
    ("ACSR",             ["ACSR", "HTGS"]),
    ("ACS",              ["ACS "]),
    ("Stranded Wire",    ["STRANDED", "STRAND"]),
    ("Weldmesh",         ["WELDMESH", "WELD MESH", "WELD-MESH"]),
    ("Barbed Wire",      ["BARBED"]),
    ("Chain Link",       ["CHAIN LINK", "CHAINLINK"]),
    ("Annealed Wire",    ["ANNEALED", "MS ANN"]),
    ("GI Wire",          ["GI WIRE", "GALVASYS", "GALVANISED", "GALVANIZED"]),
    ("MS Wire",          ["MS WIRE", " MS ", "MS BAILING", "RCA BUNDLE WIRE-MS"]),
    ("RCA Wire",         ["RCA "]),
]

# Junk/byproduct strings to exclude from the catalog entirely.
EXCLUDED_KEYWORDS = [
    "MILL SCALE", "ZINC DROSS", "PROCESSING CHARGE", "PROCESS CHARGE",
    "JOB WORK", "CONVERSION", "FREIGHT", "SCRAP", "TESTING",
]


def is_excluded(text: str) -> bool:
    upper = text.upper()
    return any(k in upper for k in EXCLUDED_KEYWORDS)


def canonical_type(text: str) -> str | None:
    if not text or is_excluded(text):
        return None
    upper = " " + text.upper() + " "  # padded so " MS " etc match
    for canon, keys in TYPE_RULES:
        if any(k in upper for k in keys):
            return canon
    return None


# ── Size extraction ─────────────────────────────────────────────────────────

# Matches '5.10 MM', '5.10mm', '5.10', '5.10 M.M.'
SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:mm|m\.m\.|M\.M\.|MM)?", re.IGNORECASE)
# Strip-style sizes: '6.1 X 1.40 MM', '4 X 0.80 MM'
STRIP_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)\s*(?:mm|MM)?")
# Stranded sizes: '7/3.15 MM', '19/2.28', etc.
STRAND_RE = re.compile(r"(\d+)\s*/\s*(\d+(?:\.\d+)?)\s*(?:mm|MM)?")
# OFC fiber count + dia: '6F 5.8 mm', '12F 7.0 MM', '48F 10.6'
OFC_RE = re.compile(r"(\d+)\s*F\b[^0-9]*?(\d+(?:\.\d+)?)\s*(?:mm|MM)?", re.IGNORECASE)


def extract_size(text: str, canon: str) -> tuple[float | None, str]:
    """
    Return (size_mm, size_label).
    size_label is human-readable; size_mm is numeric for sorting.
    """
    if not text:
        return None, ""

    # OFC: special — fiber count drives the variant
    if canon == "OFC Cable":
        m = OFC_RE.search(text)
        if m:
            f, dia = int(m.group(1)), float(m.group(2))
            if 2 <= dia <= 30:
                return dia, f"{f}F {dia:g} mm"
        return None, ""

    # Strands like 7/3.15
    if canon in ("ACSR", "ACS", "Stranded Wire"):
        m = STRAND_RE.search(text)
        if m:
            n, dia = int(m.group(1)), float(m.group(2))
            if 0.5 <= dia <= 10:
                return dia, f"{n}/{dia:g} mm"
        # fallthrough — single dimension

    # GI/MS Strip: '6.1 x 1.40 mm'
    if canon == "GI Strip":
        m = STRIP_RE.search(text)
        if m:
            w, t = float(m.group(1)), float(m.group(2))
            if 0.5 <= w <= 50 and 0.3 <= t <= 10:
                return t, f"{w:g} x {t:g} mm"

    # Single-dimension sizes (most wire products)
    for tok in SIZE_RE.findall(text):
        v = float(tok)
        if 0.3 <= v <= 30:
            return v, f"{v:.2f} mm"

    return None, ""


# ── HSN / UoM defaults ──────────────────────────────────────────────────────

UOM_DEFAULTS = {
    "OFC Cable":  "KME",
    "OPGW":       "KME",
    "HC Patented Wire": "MTS",
}
HSN_DEFAULTS = {
    "OFC Cable":  "90011000",
    "OPGW":       "90011000",
}


def default_uom(canon: str) -> str:
    return UOM_DEFAULTS.get(canon, "MT")


def default_hsn(canon: str) -> str:
    return HSN_DEFAULTS.get(canon, "722990")


# ── Mining ──────────────────────────────────────────────────────────────────

def fetch_all(table: str, columns: str, batch: int = 1000) -> list[dict]:
    """Fetch rows in batches because Supabase caps single requests at 1000."""
    rows: list[dict] = []
    start = 0
    while True:
        res = sb.table(table).select(columns).range(start, start + batch - 1).execute()
        if not res.data:
            break
        rows.extend(res.data)
        if len(res.data) < batch:
            break
        start += batch
    return rows


def mine_transactions() -> dict[tuple[str, str], dict]:
    """
    Returns map of (canonical_type, size_label) → {size_mm, sample_texts, count}.
    """
    print("📥 Fetching transactional product strings...")

    invoices     = fetch_all("invoices",     "prod_code")
    sales_orders = fetch_all("sales_orders", "prod_code")
    enquiries    = fetch_all("enquiries",    "product_desc")

    print(f"   invoices: {len(invoices)}, sales_orders: {len(sales_orders)}, enquiries: {len(enquiries)}")

    seen: dict[tuple[str, str], dict] = {}

    def consume(text: str | None):
        if not text or not text.strip():
            return
        canon = canonical_type(text)
        if not canon:
            return
        size_mm, size_label = extract_size(text, canon)
        if not size_label:
            return
        key = (canon, size_label)
        if key not in seen:
            seen[key] = {"size_mm": size_mm, "samples": [text], "count": 1}
        else:
            seen[key]["count"] += 1
            if len(seen[key]["samples"]) < 3:
                seen[key]["samples"].append(text)

    for r in invoices:     consume(r.get("prod_code"))
    for r in sales_orders: consume(r.get("prod_code"))
    for r in enquiries:    consume(r.get("product_desc"))

    print(f"   → {len(seen)} unique canonical products discovered")
    return seen


# ── Build & persist ─────────────────────────────────────────────────────────

def build_products(seen: dict[tuple[str, str], dict]) -> dict[tuple[str, str], int]:
    """
    Insert canonical products and return {(type, size_label): id} map.
    """
    print("\n🏗️  Building canonical products table...")
    rows = []
    for (canon, label), info in sorted(seen.items()):
        rows.append({
            "product_type":    canon,
            "size_mm":         info["size_mm"],
            "size_label":      label,
            "grade":           None,
            "unit_of_measure": default_uom(canon),
            "display_name":    f"{canon} {label}",
            "hsn_code":        default_hsn(canon),
            "gst_pct":         18.0,
            "is_active":       True,
        })

    # Bulk insert — table is empty after migration 004.
    inserted: list[dict] = []
    for i in range(0, len(rows), 200):
        batch = rows[i:i+200]
        res = sb.table("products").insert(batch).execute()
        inserted.extend(res.data or [])
        print(f"   inserted {len(inserted)}/{len(rows)}", end="\r")
    print(f"   ✅ {len(inserted)} canonical products inserted          ")

    # Build name→id map
    return {(p["product_type"], p["size_label"]): p["id"] for p in inserted}


# ── Re-link transactions ────────────────────────────────────────────────────

def relink_transactions(name_to_id: dict[tuple[str, str], int]):
    """
    For each table, recompute product_id from the same prod_code/desc field,
    then UPDATE in batches. Uses one UPDATE per row (no other clean way without
    a temp table) — fine since we have ~11k transactional rows total.
    """
    print("\n🔗 Re-linking transactions to canonical products...")

    def resolve(text: str | None) -> int | None:
        if not text:
            return None
        canon = canonical_type(text)
        if not canon:
            return None
        _, label = extract_size(text, canon)
        if not label:
            return None
        return name_to_id.get((canon, label))

    def update_table(table: str, text_col: str):
        rows = fetch_all(table, f"id, {text_col}")
        # Group by resolved product_id so we can UPDATE many ids in one shot
        buckets: dict[int | None, list[int]] = defaultdict(list)
        for r in rows:
            pid = resolve(r.get(text_col))
            buckets[pid].append(r["id"])

        total_resolved = sum(len(v) for k, v in buckets.items() if k is not None)
        total = len(rows)
        print(f"   {table}: {total_resolved}/{total} resolved ({100*total_resolved/total:.1f}%)")

        for pid, ids in buckets.items():
            if pid is None:
                continue
            # UPDATE in chunks of 500 ids per IN clause
            for i in range(0, len(ids), 500):
                chunk = ids[i:i+500]
                sb.table(table).update({"product_id": pid}).in_("id", chunk).execute()

    update_table("invoices",     "prod_code")
    update_table("sales_orders", "prod_code")
    update_table("enquiries",    "product_desc")


# ── FG inventory re-link ────────────────────────────────────────────────────

def relink_fg(name_to_id: dict[tuple[str, str], int]):
    """FG inventory has structured product_type + size_label, so re-link directly."""
    print("\n🔗 Re-linking fg_inventory...")
    rows = fetch_all("fg_inventory", "id, product_type, size_label")
    matched = 0
    for r in rows:
        ptype = (r.get("product_type") or "").strip()
        slabel = (r.get("size_label") or "").strip()
        canon = canonical_type(ptype) or canonical_type(slabel)
        if not canon:
            continue
        size_mm, label = extract_size(slabel, canon)
        if not label:
            continue
        pid = name_to_id.get((canon, label))
        if pid:
            sb.table("fg_inventory").update({"product_id": pid}).eq("id", r["id"]).execute()
            matched += 1
    print(f"   {matched}/{len(rows)} FG rows linked")


# ── RMS enrichment ──────────────────────────────────────────────────────────

def populate_rms_enrichment(name_to_id: dict[tuple[str, str], int]):
    print("\n📚 Populating product_rms_specs from rms_specs.json...")
    path = os.path.join(DATA_DIR, "rms_specs.json")
    if not os.path.exists(path):
        print(f"   ⚠️  {path} not found — skipping enrichment")
        return
    with open(path) as f:
        raw = json.load(f)

    rows = []
    matched = 0
    for r in raw:
        order_no = (r.get("order_no") or "").strip()
        if not order_no:
            continue
        rms_type = (r.get("product_type") or "").strip()
        canon = canonical_type(rms_type) or canonical_type(order_no)
        pid = None
        if canon:
            _, label = extract_size(order_no, canon)
            if label:
                pid = name_to_id.get((canon, label))
        if pid:
            matched += 1
        try:
            erp_id = int(r.get("order_id", 0)) or None
        except Exception:
            erp_id = None
        rows.append({
            "product_id":       pid,
            "erp_order_id":     erp_id,
            "rms_order_no":     order_no[:300],
            "rms_product_type": rms_type[:100] or None,
            "is_active":        r.get("isactive", "Yes") == "Yes",
        })

    for i in range(0, len(rows), 200):
        sb.table("product_rms_specs").insert(rows[i:i+200]).execute()
        print(f"   inserted {min(i+200, len(rows))}/{len(rows)}", end="\r")
    print(f"   ✅ {len(rows)} RMS rows loaded ({matched} linked to canonical products)")


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 Rebuild Canonical Products — sourced from transactions")
    print("=" * 65)

    # Sanity check — products table must be empty (migration 004 must have run)
    res = sb.table("products").select("id", count="exact").limit(1).execute()
    if res.count and res.count > 0:
        print(f"❌ products table is not empty ({res.count} rows). "
              "Run migration 004 first (drops & recreates products).")
        sys.exit(1)

    seen = mine_transactions()
    name_to_id = build_products(seen)
    relink_transactions(name_to_id)
    relink_fg(name_to_id)
    populate_rms_enrichment(name_to_id)

    # Deactivate products that have never been invoiced or ordered.
    # Enquiry-only or unmatched products stay in the catalog but won't appear
    # in the dashboard dropdown (which filters by is_active = true).
    print("\n🚫 Marking unsold products as inactive...")
    inv_ids = {r["product_id"] for r in fetch_all("invoices",     "product_id") if r.get("product_id")}
    so_ids  = {r["product_id"] for r in fetch_all("sales_orders", "product_id") if r.get("product_id")}
    active_ids = inv_ids | so_ids
    all_pids = [r["id"] for r in fetch_all("products", "id")]
    inactive = [pid for pid in all_pids if pid not in active_ids]
    for i in range(0, len(inactive), 500):
        chunk = inactive[i:i+500]
        sb.table("products").update({"is_active": False}).in_("id", chunk).execute()
    print(f"   {len(active_ids)} active, {len(inactive)} inactive")

    # Summary
    print("\n" + "=" * 65)
    print("📊 Final coverage:")
    for tbl in ["invoices", "sales_orders", "enquiries", "fg_inventory"]:
        total = sb.table(tbl).select("id", count="exact").limit(1).execute().count or 0
        resolved = sb.table(tbl).select("id", count="exact").not_.is_("product_id", "null").limit(1).execute().count or 0
        pct = (100 * resolved / total) if total else 0
        print(f"   {tbl:18s} {resolved:>5,}/{total:<5,} = {pct:.1f}%")

    p_count = sb.table("products").select("id", count="exact").limit(1).execute().count or 0
    rms_count = sb.table("product_rms_specs").select("id", count="exact").limit(1).execute().count or 0
    print(f"   products           {p_count:>5,} canonical SKUs")
    print(f"   product_rms_specs  {rms_count:>5,} enrichment rows")
    print("=" * 65)
