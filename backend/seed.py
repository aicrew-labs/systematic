"""
Seed script — populates the SQLite database with real + synthetic data.

Data sources:
  - CRM Dashboard.xlsx → Customer names + order counts
  - Master prompt → Product master, RM prices, machine master
  - Synthetic → 150 quote history rows with realistic pricing
  - MIS files → FG stock summaries
"""
import os
import sys
import random
from datetime import date, timedelta

import pandas as pd

# Add parent to path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, SessionLocal, init_db, Base
from app.models import Product, Customer, QuoteHistory, FGInventory, Machine, RMPrice


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)))  # Systematic/ root


def seed_all():
    """Run all seed functions."""
    print("🔧 Initializing database...")
    # Drop and recreate all tables for a clean seed
    Base.metadata.drop_all(bind=engine)
    init_db()

    db = SessionLocal()
    try:
        seed_products(db)
        seed_customers(db)
        seed_rm_prices(db)
        seed_machines(db)
        seed_fg_inventory(db)
        seed_quote_history(db)
        db.commit()
        print("✅ Database seeded successfully!")
        print(f"   Products:      {db.query(Product).count()}")
        print(f"   Customers:     {db.query(Customer).count()}")
        print(f"   Quote History: {db.query(QuoteHistory).count()}")
        print(f"   FG Inventory:  {db.query(FGInventory).count()}")
        print(f"   Machines:      {db.query(Machine).count()}")
        print(f"   RM Prices:     {db.query(RMPrice).count()}")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


# ── Products ────────────────────────────────────────────────────────────────

def seed_products(db):
    """Insert ~50 products from master prompt Section 4.5."""
    print("📦 Seeding products...")

    ms_sizes = [
        1.10, 1.18, 1.25, 1.38, 1.45, 1.52, 1.58, 1.60, 1.70, 1.80,
        1.90, 2.00, 2.10, 2.12, 2.20, 2.23, 2.25, 2.28, 2.32, 2.38,
        2.42, 2.45, 2.49, 2.58, 2.60, 2.62, 2.70, 2.80, 2.90, 2.98,
        3.00, 3.13, 3.15, 3.94, 5.58, 6.00, 6.78, 7.78,
    ]
    for s in ms_sizes:
        db.add(Product(
            product_type="MS Wire",
            size_mm=s,
            size_label=f"{s:.2f} MM",
            grade="IS 7887 G-4",
            unit_of_measure="MT",
            display_name=f"MS Wire {s:.2f}mm",
            hsn_code="722990",
            gst_pct=18.0,
        ))

    hc_sizes = [4.90, 5.10, 5.68]
    for s in hc_sizes:
        db.add(Product(
            product_type="HC Patented Wire",
            size_mm=s,
            size_label=f"{s:.2f} MM",
            grade="HC72B",
            unit_of_measure="MTS",
            display_name=f"HC Patented Wire {s:.2f}mm",
            hsn_code="722990",
            gst_pct=18.0,
        ))

    gi_sizes = [0.80, 0.90, 1.00, 1.25, 1.40, 1.60, 2.00]
    for s in gi_sizes:
        db.add(Product(
            product_type="GI Wire",
            size_mm=s,
            size_label=f"{s:.2f} MM IS",
            grade="IS",
            unit_of_measure="MT",
            display_name=f"GI Wire {s:.2f}mm IS",
            hsn_code="722990",
            gst_pct=18.0,
        ))

    ofc_products = [
        ("2F 4.5mm DIA FRP & Yarn", 4.5, "2F FRP Yarn"),
        ("4F UT UA 5.8mm FRP With Yarn", 5.8, "4F FRP Yarn"),
        ("6F UT UA 5.8mm FRP With Yarn", 5.8, "6F FRP Yarn"),
    ]
    for label, size, grade in ofc_products:
        db.add(Product(
            product_type="OFC Cable",
            size_mm=size,
            size_label=label,
            grade=grade,
            unit_of_measure="KME",
            display_name=f"OFC Cable {label}",
            hsn_code="90011000",
            gst_pct=18.0,
        ))

    db.flush()
    print(f"   → {len(ms_sizes) + len(hc_sizes) + len(gi_sizes) + len(ofc_products)} products")


# ── Customers ───────────────────────────────────────────────────────────────

def seed_customers(db):
    """Parse CRM file to extract real customer names."""
    print("👥 Seeding customers from CRM...")

    crm_path = os.path.join(DATA_DIR, "CRM  Dashboard.xlsx")
    if not os.path.exists(crm_path):
        print("   ⚠️  CRM file not found, using sample customers")
        _seed_sample_customers(db)
        return

    df = pd.read_excel(crm_path, header=1, engine="openpyxl")

    # Group by customer
    customer_stats = df.groupby("Customer Name").agg(
        total_orders=("Sales Order ID", "count"),
        total_qty=("Total Qty", "sum"),
        dispatched_qty=("Dispatch Qty", "sum"),
        sales_rep=("R.M", "first"),
    ).reset_index()

    for _, row in customer_stats.iterrows():
        name = str(row["Customer Name"]).strip()
        if not name or name == "nan":
            continue
        db.add(Customer(
            name=name,
            total_orders=int(row["total_orders"]),
            total_qty_mt=float(row["total_qty"]) if pd.notna(row["total_qty"]) else 0,
            dispatched_qty_mt=float(row["dispatched_qty"]) if pd.notna(row["dispatched_qty"]) else 0,
            is_repeat=int(row["total_orders"]) >= 2,
            sales_rep=str(row["sales_rep"]) if pd.notna(row["sales_rep"]) else None,
        ))

    db.flush()
    print(f"   → {customer_stats.shape[0]} customers from CRM")


def _seed_sample_customers(db):
    """Fallback if CRM file is missing."""
    names = [
        "Polycab India Ltd", "Diamond Power Infrastructure Ltd",
        "Fort Gloster Industries Ltd", "KEI Industries Ltd",
        "Chandresh Cables Ltd", "TRANSRAIL LIGHTING LTD",
        "Sterlite Technologies Ltd", "Maccaferri Environmental Solutions",
    ]
    for name in names:
        db.add(Customer(
            name=name, total_orders=random.randint(1, 15),
            total_qty_mt=random.uniform(10, 500), is_repeat=True,
        ))
    db.flush()


# ── RM Prices ───────────────────────────────────────────────────────────────

def seed_rm_prices(db):
    """Hardcoded RM prices from master prompt Section 4.4."""
    print("💰 Seeding RM prices...")

    prices = [
        ("Rashmi Metallurgical", 5.5, "IS 7887 G-4", 53000),
        ("Shyam Metalics", 5.5, "IS 7887 G-4", 52250),
        ("SKS Ispat", 5.5, "IS 7887 G-4", 52000),
        ("TATA Steel", 5.5, "HC72B", 67000),
        ("JSW Steel", 5.5, "CAQ G-1", 52500),
        ("Jindal", 8.5, "IS 7887 G-3", 53500),
    ]
    for vendor, size, grade, rate in prices:
        db.add(RMPrice(
            vendor_name=vendor,
            rm_size_mm=size,
            rm_grade=grade,
            rate_per_mt_inr=rate,
            effective_date=date(2026, 5, 1),
        ))
    db.flush()
    print(f"   → {len(prices)} RM prices")


# ── Machines ────────────────────────────────────────────────────────────────

def seed_machines(db):
    """Machine master from master prompt — machines with current utilisation."""
    print("⚙️  Seeding machines...")

    machines = [
        # Sayli — Medium drawing
        ("Sayli", "MS1", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 72),
        ("Sayli", "MS2", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 68),
        ("Sayli", "MS3", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 81),
        ("Sayli", "MS4", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 75),
        ("Sayli", "MS5", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 65),
        ("Sayli", "MS6", "medium_drawing", "MS Wire", 2.0, 8.0, 18, 70),
        ("Sayli", "MS7", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 78),
        ("Sayli", "MS8", "medium_drawing", "MS Wire", 2.0, 6.0, 18, 60),
        # Sayli — Fine drawing
        ("Sayli", "F1", "fine_drawing", "MS Wire", 0.9, 2.5, 8, 82),
        ("Sayli", "F2", "fine_drawing", "MS Wire", 0.9, 2.5, 8, 75),
        ("Sayli", "F3", "fine_drawing", "MS Wire", 0.9, 2.5, 8, 88),
        ("Sayli", "F4", "fine_drawing", "MS Wire", 0.9, 2.5, 8, 71),
        ("Sayli", "F5", "fine_drawing", "MS Wire", 0.9, 2.5, 8, 66),
        ("Sayli", "F6", "fine_drawing", "MS Wire", 0.9, 2.5, 8, 79),
        ("Sayli", "F7", "fine_drawing", "MS Wire", 0.9, 2.5, 8, 84),
        ("Sayli", "F8", "fine_drawing", "MS Wire", 0.9, 2.5, 8, 73),
        # Sayli — WRC
        ("Sayli", "WRC1", "wire_rod_coiler", "MS Wire", 5.5, 5.5, 20, 85),
        ("Sayli", "WRC2", "wire_rod_coiler", "MS Wire", 5.5, 5.5, 20, 78),
        ("Sayli", "WRC3", "wire_rod_coiler", "MS Wire", 5.5, 5.5, 20, 82),
        # Veritas Unit 1 — HC drawing
        ("Veritas Unit 1", "U1-HC-8B1", "hc_drawing", "HC Patented Wire", 0.3, 6.0, 12, 74),
        ("Veritas Unit 1", "U1-HC-7B1", "hc_drawing", "HC Patented Wire", 0.3, 6.0, 12, 68),
        ("Veritas Unit 1", "U1-HC-11B1", "hc_drawing", "HC Patented Wire", 0.3, 6.0, 12, 81),
        ("Veritas Unit 1", "U1-HC-6B1", "hc_drawing", "HC Patented Wire", 0.3, 6.0, 12, 72),
        # Veritas Unit 2 — Fine GI
        ("Veritas Unit 2", "U2-GI-L1", "galvanising", "GI Wire", 0.8, 2.0, 10, 76),
        ("Veritas Unit 2", "U2-GI-L2", "galvanising", "GI Wire", 0.8, 2.0, 10, 70),
        ("Veritas Unit 2", "U2-GI-L3", "galvanising", "GI Wire", 0.8, 2.0, 10, 82),
        # Veritas Unit 3 — Heavy GI
        ("Veritas Unit 3", "U3-GS-L1", "galvanising", "GI Wire", 2.0, 4.0, 14, 65),
        ("Veritas Unit 3", "U3-GS-L2", "galvanising", "GI Wire", 2.0, 4.0, 14, 72),
        # Veritas Unit 4 — FCA/RCA
        ("Veritas Unit 4", "U4-FCA-1", "galvanising", "GI Wire", 0.8, 3.0, 12, 77),
        ("Veritas Unit 4", "U4-RCA-1", "galvanising", "GI Wire", 2.0, 4.0, 12, 69),
    ]

    for unit, code, mtype, ptypes, min_d, max_d, cap, util in machines:
        db.add(Machine(
            unit_name=unit, machine_code=code, machine_type=mtype,
            product_types=ptypes, min_dia_mm=min_d, max_dia_mm=max_d,
            capacity_mt_per_day=cap, current_utilisation_pct=util,
        ))
    db.flush()
    print(f"   → {len(machines)} machines")


# ── FG Inventory ────────────────────────────────────────────────────────────

def seed_fg_inventory(db):
    """Load FG stock from MIS STOCK sheets."""
    print("📊 Seeding FG inventory...")

    today = date.today()

    # Aggregate stock from MIS files
    fg_data = [
        # Sayli — MS Wire FG (estimated from Daily Inventory sheet)
        ("Sayli", "MS Wire", "1.38 MM", 8.5),
        ("Sayli", "MS Wire", "1.58 MM", 12.3),
        ("Sayli", "MS Wire", "2.12 MM", 6.7),
        ("Sayli", "MS Wire", "2.49 MM", 15.2),
        ("Sayli", "MS Wire", "2.62 MM", 22.4),
        ("Sayli", "MS Wire", "2.98 MM", 9.1),
        ("Sayli", "MS Wire", "3.13 MM", 11.8),
        ("Sayli", "MS Wire", "5.58 MM", 18.6),
        # Veritas Unit 1 — ACSR/HC
        ("Veritas Unit 1", "HC Patented Wire", "5.10 MM", 14.2),
        ("Veritas Unit 1", "HC Patented Wire", "5.68 MM", 8.7),
        ("Veritas Unit 1", "HC Patented Wire", "4.90 MM", 6.3),
        # Veritas Unit 2 — Fine GI
        ("Veritas Unit 2", "GI Wire", "0.80 MM IS", 7.2),
        ("Veritas Unit 2", "GI Wire", "0.90 MM IS", 34.5),
        ("Veritas Unit 2", "GI Wire", "1.00 MM IS", 5.8),
        ("Veritas Unit 2", "GI Wire", "1.25 MM IS", 28.7),
        ("Veritas Unit 2", "GI Wire", "1.40 MM IS", 12.1),
        ("Veritas Unit 2", "GI Wire", "1.60 MM IS", 8.9),
        # Veritas Unit 3 — Heavy GI
        ("Veritas Unit 3", "GI Wire", "2.00 MM IS", 15.3),
        # Veritas Unit 4 — GI Strip/Wire
        ("Veritas Unit 4", "GI Wire", "2.00 MM IS", 8.5),
        # OFC — not tracked in MIS currently
        ("Veritas Unit 1", "OFC Cable", "2F 4.5mm DIA FRP & Yarn", 2.5),
        ("Veritas Unit 1", "OFC Cable", "4F UT UA 5.8mm FRP With Yarn", 1.8),
        ("Veritas Unit 1", "OFC Cable", "6F UT UA 5.8mm FRP With Yarn", 0.9),
    ]

    for unit, ptype, slabel, qty in fg_data:
        db.add(FGInventory(
            snapshot_date=today, unit_name=unit, product_type=ptype,
            size_label=slabel, quantity_mt=qty, inventory_type="FG",
        ))

    db.flush()
    print(f"   → {len(fg_data)} FG inventory entries")


# ── Quote History (Synthetic) ───────────────────────────────────────────────

def seed_quote_history(db):
    """Generate 150 synthetic quote history rows per master prompt Section 7."""
    print("📜 Seeding synthetic quote history...")

    random.seed(42)  # Reproducible

    customers = [
        "Systematic Industries Ltd - Sarigam",
        "Polycab India Ltd - Daman",
        "Diamond Power Infrastructure Ltd",
        "Fort Gloster Industries Ltd",
        "Shree Hanuman Tubes Pvt Ltd",
        "Maccaferri Environmental Solutions",
        "TRANSRAIL LIGHTING LTD",
        "Chandresh Cables Ltd",
        "KEI Industries Ltd",
        "Nirmal Networks",
        "Cisfiber Infra Solution",
        "Ascent Networks Pvt Ltd",
        "Al Ma Cabrol FZC LLC",
        "A-1 Fence Products Company Pvt Ltd - Unit II",
    ]

    products_rates = [
        ("MS Wire", "2.62 MM", "MT", 58000, 63000),
        ("MS Wire", "1.38 MM", "MT", 61000, 66000),
        ("MS Wire", "5.58 MM", "MT", 55000, 59000),
        ("MS Wire", "2.49 MM", "MT", 57000, 62000),
        ("MS Wire", "2.98 MM", "MT", 56000, 61000),
        ("HC Patented Wire", "5.10 MM", "MTS", 87000, 93000),
        ("HC Patented Wire", "5.68 MM", "MTS", 87000, 92000),
        ("HC Patented Wire", "4.90 MM", "MTS", 88000, 94000),
        ("GI Wire", "0.90 MM IS", "MT", 72000, 78000),
        ("GI Wire", "1.25 MM IS", "MT", 70000, 75000),
        ("OFC Cable", "2F 4.5mm DIA FRP & Yarn", "KME", 3700, 4200),
        ("OFC Cable", "4F UT UA 5.8mm FRP With Yarn", "KME", 6500, 7500),
        ("OFC Cable", "6F UT UA 5.8mm FRP With Yarn", "KME", 8500, 9500),
    ]

    payment_terms_list = ["Advance", "30 Days", "45 Days", "60 Days"]
    sales_reps = ["Rahul Giri", "Ravi Kumar", "Amit Shah", "Sanjay Patel", "Vikram Singh"]

    rows = []
    base_date = date(2026, 4, 1)

    for i in range(150):
        cust = random.choice(customers)
        ptype, slabel, unit, rate_low, rate_high = random.choice(products_rates)

        # Won/lost distribution: 70% won, 30% lost
        # Lost quotes tend to be at higher end
        is_won = random.random() < 0.70
        if is_won:
            rate = random.uniform(rate_low, rate_low + (rate_high - rate_low) * 0.7)
        else:
            rate = random.uniform(rate_low + (rate_high - rate_low) * 0.4, rate_high)

        rate = round(rate, 0)
        qty = round(random.uniform(2, 100), 1) if unit == "MT" else round(random.uniform(1, 50), 1)
        q_date = base_date + timedelta(days=random.randint(0, 45))
        terms = random.choice(payment_terms_list)
        credit_days = {"Advance": 0, "30 Days": 30, "45 Days": 45, "60 Days": 60}[terms]

        db.add(QuoteHistory(
            quote_date=q_date,
            customer_name=cust,
            product_type=ptype,
            size_label=slabel,
            grade=None,
            quantity=qty,
            unit=unit,
            unit_rate_inr=rate,
            net_amount_inr=round(rate * qty, 2),
            payment_terms=terms,
            credit_days=credit_days,
            outcome="won" if is_won else "lost",
            sales_rep=random.choice(sales_reps),
            notes=None,
        ))

    db.flush()
    print(f"   → 150 synthetic quote history rows")


if __name__ == "__main__":
    seed_all()
