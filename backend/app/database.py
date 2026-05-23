"""
Supabase data layer for Quote Intelligence.
Path 2: pure Supabase, no JSON fallback, no legacy fields.
"""
from __future__ import annotations
import os
from typing import Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in the environment "
        "(see .env.example)."
    )

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Warning: Failed to initialize Supabase client: {e}")
    supabase = None  # type: ignore[assignment]


# ── Customers ──────────────────────────────────────────────────────────────

def list_customers() -> list[dict]:
    """All customers, ordered by total_orders desc then name."""
    if not supabase:
        return []
    res = (
        supabase.table("customers")
        .select("id, name, total_orders, is_repeat")
        .order("total_orders", desc=True)
        .order("name")
        .limit(2000)
        .execute()
    )
    return res.data or []


def get_customer(customer_id: int) -> dict | None:
    if not supabase:
        return None
    res = (
        supabase.table("customers")
        .select("id, name, total_orders, is_repeat, sales_rep")
        .eq("id", customer_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


# ── Products ───────────────────────────────────────────────────────────────

def list_products() -> list[dict]:
    """All active products, raw rows."""
    if not supabase:
        return []
    res = (
        supabase.table("products")
        .select("id, product_type, size_mm, size_label, unit_of_measure, is_active")
        .eq("is_active", True)
        .order("product_type")
        .order("size_mm")
        .limit(5000)
        .execute()
    )
    return res.data or []


def get_product(product_id: int) -> dict | None:
    if not supabase:
        return None
    res = (
        supabase.table("products")
        .select("id, product_type, size_mm, size_label, unit_of_measure, grade")
        .eq("id", product_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


# ── Invoices (won deals) ───────────────────────────────────────────────────

def invoices_for_product(product_id: int, limit: int = 20) -> list[dict]:
    if not supabase:
        return []
    res = (
        supabase.table("invoices")
        .select("invoice_date, customer_name, customer_id, prod_code, "
                "quantity, unit, unit_rate, prod_total, outcome, "
                "erp_inv_nos, erp_so_no")
        .eq("product_id", product_id)
        .eq("outcome", "won")
        .order("invoice_date", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def invoices_for_customer(customer_id: int, limit: int = 20) -> list[dict]:
    if not supabase:
        return []
    res = (
        supabase.table("invoices")
        .select("invoice_date, customer_name, prod_code, product_id, "
                "quantity, unit, unit_rate, prod_total, outcome, "
                "erp_inv_nos, erp_so_no")
        .eq("customer_id", customer_id)
        .eq("outcome", "won")
        .order("invoice_date", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def invoice_lookup_for_product(product_id: int) -> dict[int, dict]:
    """
    For status-promotion: most recent (erp_inv_nos, erp_so_no, date) per customer,
    keyed by customer_id. Used when an enquiry is promoted to 'Won'.
    """
    if not supabase:
        return {}
    res = (
        supabase.table("invoices")
        .select("customer_id, erp_inv_nos, erp_so_no, invoice_date")
        .eq("product_id", product_id)
        .eq("outcome", "won")
        .order("invoice_date", desc=True)
        .limit(5000)
        .execute()
    )
    lookup: dict[int, dict] = {}
    for r in (res.data or []):
        cid = r.get("customer_id")
        if cid and cid not in lookup:   # first row wins (already ordered desc)
            lookup[cid] = {
                "invoice_no": r.get("erp_inv_nos"),
                "so_no":      r.get("erp_so_no"),
            }
    return lookup


# ── Sales orders (in-progress) ─────────────────────────────────────────────

def sales_order_lookup_for_product(product_id: int) -> dict[int, dict]:
    """
    For status-promotion: most recent erp_so_no per customer.
    Used when an enquiry is promoted to 'In Progress'.
    """
    if not supabase:
        return {}
    res = (
        supabase.table("sales_orders")
        .select("customer_id, erp_so_no, order_date")
        .eq("product_id", product_id)
        .order("order_date", desc=True)
        .limit(5000)
        .execute()
    )
    lookup: dict[int, dict] = {}
    for r in (res.data or []):
        cid = r.get("customer_id")
        if cid and cid not in lookup:
            lookup[cid] = {"so_no": r.get("erp_so_no")}
    return lookup


# ── Enquiries (all signals) ────────────────────────────────────────────────

def enquiries_for_product(product_id: int, limit: int = 50) -> list[dict]:
    if not supabase:
        return []
    res = (
        supabase.table("enquiries")
        .select("enquiry_date, customer_name, customer_id, product_desc, "
                "quantity, unit, price_offered, status")
        .eq("product_id", product_id)
        .order("enquiry_date", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


# ── FG inventory ───────────────────────────────────────────────────────────

def fg_for_product(product_id: int) -> list[dict]:
    if not supabase:
        return []
    res = (
        supabase.table("fg_inventory")
        .select("quantity_mt, unit_name, inventory_type")
        .eq("product_id", product_id)
        .eq("inventory_type", "FG")
        .execute()
    )
    return res.data or []


# ── Machines ───────────────────────────────────────────────────────────────

def machines_by_type(machine_type: str) -> list[dict]:
    if not supabase:
        return []
    res = (
        supabase.table("machines")
        .select("current_utilisation_pct, capacity_mt_per_day, unit_name, machine_code")
        .eq("machine_type", machine_type)
        .eq("active", True)
        .execute()
    )
    return res.data or []


# ── RM prices ──────────────────────────────────────────────────────────────

def rm_price_for_grade(rm_grade: str) -> dict | None:
    if not supabase:
        return None
    res = (
        supabase.table("rm_prices")
        .select("rate_per_mt_inr, vendor_name, rm_grade")
        .eq("rm_grade", rm_grade)
        .order("effective_date", desc=True)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


# ── Daily rates ────────────────────────────────────────────────────────────

DEFAULT_RATES = {
    "ms_steel_rate": 52000.0,
    "hc_steel_rate": 67000.0,
    "zinc_rate":     260.0,
}


def get_daily_rates() -> dict:
    if not supabase:
        return dict(DEFAULT_RATES)
    try:
        res = (
            supabase.table("daily_rates")
            .select("ms_steel_rate, hc_steel_rate, zinc_rate")
            .order("rate_date", desc=True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if res.data:
            return {
                "ms_steel_rate": float(res.data[0]["ms_steel_rate"]),
                "hc_steel_rate": float(res.data[0]["hc_steel_rate"]),
                "zinc_rate":     float(res.data[0]["zinc_rate"]),
            }
    except Exception as e:
        print(f"Error fetching daily_rates: {e}")
    return dict(DEFAULT_RATES)


def insert_daily_rates(rates: dict[str, Any]) -> dict:
    if not supabase:
        return rates
    row = {
        "ms_steel_rate": float(rates["ms_steel_rate"]),
        "hc_steel_rate": float(rates["hc_steel_rate"]),
        "zinc_rate":     float(rates["zinc_rate"]),
        "entered_by":    "FastAPI Backend",
    }
    try:
        supabase.table("daily_rates").insert(row).execute()
    except Exception as e:
        print(f"Error inserting daily_rates: {e}")
    return get_daily_rates()
