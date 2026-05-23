"""
SQLAlchemy ORM models for Quote Intelligence — Schema v2
ERP-synced schema with proper foreign keys.
"""
from datetime import date, datetime
from sqlalchemy import (
    String, Float, Integer, Boolean, Date, DateTime,
    Text, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


# ── Master Tables ────────────────────────────────────────────────────────────

class Product(Base):
    """ERP RMS product catalog — PK = ERP order_id."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)  # ERP order_id
    product_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_mm: Mapped[float] = mapped_column(Float, nullable=True)
    size_label: Mapped[str] = mapped_column(String(200), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(10), nullable=False, default="MT")
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hsn_code: Mapped[str] = mapped_column(String(20), nullable=True)
    gst_pct: Mapped[float] = mapped_column(Float, nullable=False, default=18.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Customer(Base):
    """ERP customer master — PK = ERP customer_id."""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)  # ERP customer_id
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=True)               # ERP company_id
    total_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_qty_mt: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dispatched_qty_mt: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_repeat: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sales_rep: Mapped[str] = mapped_column(String(100), nullable=True)


class ManufacturingUnit(Base):
    """Internal master for factory units — Sayli, Veritas Unit 1, etc."""
    __tablename__ = "manufacturing_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    billing_code: Mapped[str] = mapped_column(String(20), nullable=True)  # SIL, VIPL, SIGM, WBIPL
    location: Mapped[str] = mapped_column(String(200), nullable=True)


# ── Transaction Tables ───────────────────────────────────────────────────────

class Enquiry(Base):
    """CRM enquiries — one row per product line item."""
    __tablename__ = "enquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    erp_id: Mapped[str] = mapped_column(String(100), nullable=True)            # ERP enquiry_no
    enquiry_date: Mapped[date] = mapped_column(Date, nullable=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=True)     # fallback
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_desc: Mapped[str] = mapped_column(Text, nullable=True)
    prod_category: Mapped[str] = mapped_column(String(100), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=True)
    price_offered: Mapped[float] = mapped_column(Float, nullable=True)
    target_price: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    sales_rep: Mapped[str] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    cust_type: Mapped[str] = mapped_column(String(50), nullable=True)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_enquiries_erp_id", "erp_id"),
        Index("idx_enquiries_customer_id", "customer_id"),
        Index("idx_enquiries_product_id", "product_id"),
        Index("idx_enquiries_date", "enquiry_date"),
    )


class SalesOrder(Base):
    """ERP sales orders — one row per product line item."""
    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    erp_so_no: Mapped[str] = mapped_column(String(50), nullable=False)          # ERP so_number
    erp_do_no: Mapped[str] = mapped_column(String(50), nullable=True)
    erp_enquiry_id: Mapped[str] = mapped_column(String(100), nullable=True)     # ref to enquiries.erp_id
    order_date: Mapped[date] = mapped_column(Date, nullable=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    prod_code: Mapped[str] = mapped_column(String(200), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=True)
    pending_qty: Mapped[float] = mapped_column(Float, nullable=True)
    dispatched_qty: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=True)
    unit_rate: Mapped[float] = mapped_column(Float, nullable=True)
    freight: Mapped[str] = mapped_column(String(50), nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(500), nullable=True)
    credit_days: Mapped[int] = mapped_column(Integer, nullable=True)
    billing_unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("manufacturing_units.id", ondelete="SET NULL"), nullable=True)
    dispatch_from: Mapped[str] = mapped_column(String(500), nullable=True)
    po_number: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    sales_rep: Mapped[str] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_so_erp_so_no", "erp_so_no"),
        Index("idx_so_customer_id", "customer_id"),
        Index("idx_so_product_id", "product_id"),
    )


class Invoice(Base):
    """ERP invoices — one row per product line item."""
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    erp_invoice_id: Mapped[str] = mapped_column(String(50), nullable=False)
    erp_inv_nos: Mapped[str] = mapped_column(String(50), nullable=True)
    erp_so_no: Mapped[str] = mapped_column(String(50), nullable=True)           # ref to sales_orders.erp_so_no
    erp_do_no: Mapped[str] = mapped_column(String(50), nullable=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    prod_code: Mapped[str] = mapped_column(String(200), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=True)
    unit_rate: Mapped[float] = mapped_column(Float, nullable=True)
    freight: Mapped[str] = mapped_column(String(50), nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(500), nullable=True)
    credit_days: Mapped[int] = mapped_column(Integer, nullable=True)
    billing_unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("manufacturing_units.id", ondelete="SET NULL"), nullable=True)
    dispatch_from: Mapped[str] = mapped_column(String(500), nullable=True)
    po_number: Mapped[str] = mapped_column(String(100), nullable=True)
    po_date: Mapped[date] = mapped_column(Date, nullable=True)
    order_status: Mapped[str] = mapped_column(String(50), nullable=True)
    voucher_type: Mapped[str] = mapped_column(String(100), nullable=True)
    cgst: Mapped[float] = mapped_column(Float, nullable=True)
    sgst: Mapped[float] = mapped_column(Float, nullable=True)
    igst: Mapped[float] = mapped_column(Float, nullable=True)
    prod_total: Mapped[float] = mapped_column(Float, nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, nullable=True)
    sales_rep: Mapped[str] = mapped_column(String(100), nullable=True)
    outcome: Mapped[str] = mapped_column(String(20), nullable=True, default="won")

    __table_args__ = (
        Index("idx_inv_erp_invoice_id", "erp_invoice_id"),
        Index("idx_inv_customer_id", "customer_id"),
        Index("idx_inv_product_id", "product_id"),
        Index("idx_inv_so_no", "erp_so_no"),
        Index("idx_inv_date", "invoice_date"),
    )


class FGInventory(Base):
    """Finished goods inventory snapshots."""
    __tablename__ = "fg_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("manufacturing_units.id", ondelete="SET NULL"), nullable=True)
    unit_name: Mapped[str] = mapped_column(String(100), nullable=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    product_type: Mapped[str] = mapped_column(String(100), nullable=True)
    size_label: Mapped[str] = mapped_column(String(100), nullable=True)
    quantity_mt: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    inventory_type: Mapped[str] = mapped_column(String(50), nullable=False, default="FG")

    __table_args__ = (
        Index("idx_fg_product_id", "product_id"),
        Index("idx_fg_unit_id", "unit_id"),
    )


class Machine(Base):
    """Machine master — linked to manufacturing unit."""
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(Integer, ForeignKey("manufacturing_units.id", ondelete="SET NULL"), nullable=True)
    unit_name: Mapped[str] = mapped_column(String(100), nullable=True)
    machine_code: Mapped[str] = mapped_column(String(50), nullable=False)
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    min_dia_mm: Mapped[float] = mapped_column(Float, nullable=True)
    max_dia_mm: Mapped[float] = mapped_column(Float, nullable=True)
    capacity_mt_per_day: Mapped[float] = mapped_column(Float, nullable=True)
    current_utilisation_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class RMPrice(Base):
    """Raw material prices — standalone."""
    __tablename__ = "rm_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rm_size_mm: Mapped[float] = mapped_column(Float, nullable=False)
    rm_grade: Mapped[str] = mapped_column(String(50), nullable=False)
    rate_per_mt_inr: Mapped[float] = mapped_column(Float, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)


class DailyRate(Base):
    """Daily steel/zinc rates — standalone user input."""
    __tablename__ = "daily_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    ms_steel_rate: Mapped[float] = mapped_column(Float, nullable=False)
    hc_steel_rate: Mapped[float] = mapped_column(Float, nullable=False)
    zinc_rate: Mapped[float] = mapped_column(Float, nullable=False)
    entered_by: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
