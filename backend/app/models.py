"""
SQLAlchemy ORM models for Quote Intelligence.
Slim schema — only tables needed for the prototype.
"""
from datetime import date, datetime
from sqlalchemy import String, Float, Integer, Boolean, Date, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_type: Mapped[str] = mapped_column(String(100))       # 'MS Wire', 'HC Patented Wire', 'GI Wire', 'OFC Cable'
    size_mm: Mapped[float] = mapped_column(Float, nullable=True) # e.g. 2.62
    size_label: Mapped[str] = mapped_column(String(100))         # e.g. '2.62 MM' or '2F 4.5mm DIA FRP & Yarn'
    grade: Mapped[str] = mapped_column(String(50), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(10))     # 'MT', 'MTS', 'KME'
    display_name: Mapped[str] = mapped_column(String(200))       # Full display: 'MS Wire 2.62mm'
    hsn_code: Mapped[str] = mapped_column(String(20), nullable=True)
    gst_pct: Mapped[float] = mapped_column(Float, default=18.0)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_qty_mt: Mapped[float] = mapped_column(Float, default=0.0)
    dispatched_qty_mt: Mapped[float] = mapped_column(Float, default=0.0)
    is_repeat: Mapped[bool] = mapped_column(Boolean, default=False)
    sales_rep: Mapped[str] = mapped_column(String(100), nullable=True)


class QuoteHistory(Base):
    __tablename__ = "quote_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quote_date: Mapped[date] = mapped_column(Date)
    customer_name: Mapped[str] = mapped_column(String(200))
    product_type: Mapped[str] = mapped_column(String(100))
    size_label: Mapped[str] = mapped_column(String(100))
    grade: Mapped[str] = mapped_column(String(50), nullable=True)
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(10))
    unit_rate_inr: Mapped[float] = mapped_column(Float)
    net_amount_inr: Mapped[float] = mapped_column(Float)
    payment_terms: Mapped[str] = mapped_column(String(50), nullable=True)
    credit_days: Mapped[int] = mapped_column(Integer, nullable=True)
    outcome: Mapped[str] = mapped_column(String(20))             # 'won', 'lost', 'pending'
    sales_rep: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class FGInventory(Base):
    __tablename__ = "fg_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(Date)
    unit_name: Mapped[str] = mapped_column(String(100))          # 'Sayli', 'Veritas Unit 1', etc.
    product_type: Mapped[str] = mapped_column(String(100))
    size_label: Mapped[str] = mapped_column(String(100))
    quantity_mt: Mapped[float] = mapped_column(Float, default=0.0)
    inventory_type: Mapped[str] = mapped_column(String(50))      # 'FG', 'B_Grade', 'Non_Moving', 'WIP'


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_name: Mapped[str] = mapped_column(String(100))
    machine_code: Mapped[str] = mapped_column(String(50))
    machine_type: Mapped[str] = mapped_column(String(50))        # 'medium_drawing', 'fine_drawing', 'galvanising', etc.
    product_types: Mapped[str] = mapped_column(String(200))      # comma-separated: 'MS Wire,HC Wire'
    min_dia_mm: Mapped[float] = mapped_column(Float, nullable=True)
    max_dia_mm: Mapped[float] = mapped_column(Float, nullable=True)
    capacity_mt_per_day: Mapped[float] = mapped_column(Float, nullable=True)
    current_utilisation_pct: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class RMPrice(Base):
    __tablename__ = "rm_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_name: Mapped[str] = mapped_column(String(100))
    rm_size_mm: Mapped[float] = mapped_column(Float)
    rm_grade: Mapped[str] = mapped_column(String(50))
    rate_per_mt_inr: Mapped[float] = mapped_column(Float)
    effective_date: Mapped[date] = mapped_column(Date)
