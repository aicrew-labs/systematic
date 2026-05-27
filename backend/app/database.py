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
        .select("id, name, total_orders, is_repeat, region_id")
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
        .select("id, name, total_orders, is_repeat, sales_rep, region_id")
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
        .select("id, product_type, size_mm, size_label, unit_of_measure, grade, cost_category_code")
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
        .select("invoice_date, customer_id, customer_name, prod_code, product_id, "
                "quantity, unit, unit_rate, prod_total, outcome, "
                "erp_inv_nos, erp_so_no, "
                "products!inner(cost_category_code)")
        .eq("customer_id", customer_id)
        .eq("outcome", "won")
        .order("invoice_date", desc=True)
        .limit(limit)
        .execute()
    )
    rows = res.data or []
    # Flatten cost_category_code from nested products join
    for row in rows:
        if isinstance(row.get("products"), dict):
            row["cost_category_code"] = row["products"].get("cost_category_code")
        row.pop("products", None)
    return rows


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
    "loading_cost_per_mt": 0.0,
    "fuel_surcharge_pct": 0.0,
    "freight_rate_per_mt_km": 0.0,
}

DAILY_RATES_COLUMNS = "prime_steel_rate, hc_steel_rate, commercial_steel_rate, zinc_sgh_rate, zinc_rate, wire_rod_rate, conv_wiping_fine_rate, conv_wiping_thick_rate, conv_heavy_fine_rate, conv_heavy_thick_rate, conv_printing_rate, conv_stranding_rate, loading_cost_per_mt, fuel_surcharge_pct, freight_rate_per_mt_km, rate_date"

def get_daily_rates() -> dict:
    if not supabase:
        return dict(DEFAULT_RATES, rate_date=None)
    try:
        res = (
            supabase.table("daily_rates")
            .select(DAILY_RATES_COLUMNS)
            .order("rate_date", desc=True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if res.data:
            row = res.data[0]
            rates = {k: float(row[k]) for k in DEFAULT_RATES.keys() if k in row}
            rates["rate_date"] = str(row["rate_date"]) if row.get("rate_date") else None
            return rates
    except Exception as e:
        print(f"Error fetching daily_rates: {e}")
    return dict(DEFAULT_RATES, rate_date=None)


def get_daily_rates_history(days: int = 7) -> list[dict]:
    """Fetch daily rates history for the last N days."""
    if not supabase:
        return []
    try:
        from datetime import date, timedelta
        start_date = (date.today() - timedelta(days=days)).isoformat()
        res = (
            supabase.table("daily_rates")
            .select(DAILY_RATES_COLUMNS)
            .gte("rate_date", start_date)
            .order("rate_date", desc=False)  # Chronological order for charting
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"Error fetching daily_rates history: {e}")
        return []


def insert_daily_rates(rates: dict[str, Any], user_id: str = "Dashboard") -> dict:
    """Upsert daily rates: update today's row if it exists, otherwise insert."""
    if not supabase:
        return rates
    from datetime import date as _date
    today = _date.today().isoformat()
    
    upsert_data = {k: float(rates[k]) for k in DEFAULT_RATES.keys() if k in rates}
    upsert_data["entered_by"] = user_id

    try:
        # Check if a row already exists for today
        existing = (
            supabase.table("daily_rates")
            .select("id")
            .eq("rate_date", today)
            .limit(1)
            .execute()
        )
        if existing.data:
            # Update the existing row
            supabase.table("daily_rates").update(upsert_data).eq("rate_date", today).execute()
        else:
            # Insert a new row for today
            upsert_data["rate_date"] = today
            supabase.table("daily_rates").insert(upsert_data).execute()
    except Exception as e:
        print(f"Error upserting daily_rates: {e}")
    return get_daily_rates()


# ── Configuration Tables ───────────────────────────────────────────────────

def list_product_cost_configs() -> list[dict]:
    if not supabase:
        return []
    try:
        res = (
            supabase.table("product_cost_config")
            .select("*")
            .order("category_name")
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"Error fetching product_cost_config: {e}")
        return []

def upsert_product_cost_config(data: dict[str, Any], user_id: str = "Dashboard") -> dict | None:
    if not supabase:
        return None
    try:
        # Check if row exists based on category_code (unique)
        existing = (
            supabase.table("product_cost_config")
            .select("id")
            .eq("category_id", data["category_id"])
            .limit(1)
            .execute()
        )
        if existing.data:
            data["updated_by"] = user_id
            res = (
                supabase.table("product_cost_config")
                .update(data)
                .eq("category_id", data["category_id"])
                .execute()
            )
        else:
            data["updated_by"] = user_id
            res = (
                supabase.table("product_cost_config")
                .insert(data)
                .execute()
            )
        return (res.data or [None])[0]
    except Exception as e:
        print(f"Error upserting product_cost_config: {e}")
        return None

def delete_product_cost_config(category_id: str) -> bool:
    if not supabase:
        return False
    try:
        res = (
            supabase.table("product_cost_config")
            .delete()
            .eq("category_id", category_id)
            .execute()
        )
        return True
    except Exception as e:
        print(f"Error deleting product_cost_config: {e}")
        return False

def get_product_cost_config(category_id: str) -> dict | None:
    if not supabase or not category_id:
        return None
    try:
        res = (
            supabase.table("product_cost_config")
            .select("*")
            .eq("category_id", category_id)
            .limit(1)
            .execute()
        )
        return (res.data or [None])[0]
    except Exception as e:
        print(f"Error fetching product_cost_config for {category_id}: {e}")
        return None

def get_location_margin_config(region_id: str) -> dict | None:
    if not supabase or not region_id:
        return None
    try:
        res = (
            supabase.table("location_margin_config")
            .select("*")
            .eq("region_id", region_id)
            .limit(1)
            .execute()
        )
        return (res.data or [None])[0]
    except Exception as e:
        print(f"Error fetching location_margin_config for {region_id}: {e}")
        return None


def invoices_for_category(category_code: str, limit: int = 20) -> list[dict]:
    # Join invoices with products to filter by cost_category_code
    resp = (
        supabase.table("invoices")
        .select("*, products!inner(cost_category_code)")
        .eq("products.cost_category_code", category_code)
        .order("invoice_date", desc=True)
        .limit(limit)
        .execute()
    )
    rows = resp.data or []
    # Flatten the nested cost_category_code onto each row for downstream use
    for row in rows:
        if isinstance(row.get("products"), dict):
            row["cost_category_code"] = row["products"].get("cost_category_code")
        row.pop("products", None)
    return rows


def list_location_margin_configs() -> list[dict]:
    if not supabase:
        return []
    try:
        res = (
            supabase.table("location_margin_config")
            .select("*")
            .eq("is_active", True)
            .limit(2000)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"Error fetching location_margin_config list: {e}")
        return []

# ── Auth ───────────────────────────────────────────────────────────────────

def get_user_by_user_id(user_id: str) -> dict | None:
    if not supabase: return None
    try:
        res = supabase.table("app_users").select("*").eq("user_id", user_id).limit(1).execute()
        return (res.data or [None])[0]
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def update_last_login(user_id: str) -> None:
    if not supabase: return
    try:
        # TIMESTAMPTZ formatting for Supabase
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        supabase.table("app_users").update({"last_login": now}).eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error updating last login: {e}")

def list_all_users() -> list[dict]:
    if not supabase: return []
    try:
        res = supabase.table("app_users").select("id, user_id, full_name, email, role, is_active, last_login, created_at").order("id").execute()
        return res.data or []
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

def create_user(data: dict) -> dict | None:
    if not supabase: return None
    try:
        res = supabase.table("app_users").insert(data).execute()
        return (res.data or [None])[0]
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def update_user(user_id: str, data: dict) -> dict | None:
    if not supabase: return None
    try:
        res = supabase.table("app_users").update(data).eq("user_id", user_id).execute()
        return (res.data or [None])[0]
    except Exception as e:
        print(f"Error updating user: {e}")
        return None
