"""
Pydantic schemas for Quote Intelligence API.
Path 2 architecture — single bundled response from /api/v1/analyze.
"""
from pydantic import BaseModel
from typing import List, Optional, Literal


# ── Read-only listings ─────────────────────────────────────────────────────

class CustomerInfo(BaseModel):
    id: int
    name: str
    total_orders: int = 0
    is_repeat: bool = False


class ProductSize(BaseModel):
    id: int
    size_label: str
    size_mm: Optional[float] = None
    unit_of_measure: str = "MT"


class ProductGroup(BaseModel):
    """Products grouped by product_type for the dashboard dropdown."""
    product_type: str
    sizes: List[ProductSize]


class DailyRatesOut(BaseModel):
    ms_steel_rate: float
    hc_steel_rate: float
    zinc_rate: float
    rate_date: Optional[str] = None   # ISO date of the latest entry e.g. '2026-05-24'


class DailyRatesInput(BaseModel):
    ms_steel_rate: float
    hc_steel_rate: float
    zinc_rate: float


# ── Configuration Models ───────────────────────────────────────────────────

class ProductCostConfigOut(BaseModel):
    id: int
    category_code: str
    category_name: str
    steel_type: str = "MS"
    steel_weight_per_mt: float
    zinc_weight_per_mt: float = 0.0
    yield_loss_pct: Optional[float] = None
    conversion_cost_per_mt: float
    packing_cost_per_mt: Optional[float] = None
    min_margin_pct: float = 10.0
    max_margin_pct: float = 15.0
    is_active: bool = True

class ProductCostConfigInput(BaseModel):
    category_code: str
    category_name: str
    steel_type: str = "MS"
    steel_weight_per_mt: float
    zinc_weight_per_mt: float = 0.0
    yield_loss_pct: Optional[float] = None
    conversion_cost_per_mt: float
    packing_cost_per_mt: Optional[float] = None
    min_margin_pct: float = 10.0
    max_margin_pct: float = 15.0
    is_active: bool = True


# ── Analyze request/response ───────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    customer_id: int
    product_id: int
    quantity: float
    payment_terms: Optional[str] = "30 Days"
    mode: Literal["ai", "algo"] = "algo"   # algo by default — no API spend


class ContextCard(BaseModel):
    label: str
    value: str
    sub_text: str = ""


class MarketSignal(BaseModel):
    color: Literal["green", "amber", "red", "blue"]
    text: str


class HistoryRow(BaseModel):
    date: Optional[str] = None
    customer_name: Optional[str] = None
    product_label: Optional[str] = None
    rate: Optional[float] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    outcome: Literal["won", "lost", "in_progress", "open"] = "open"
    # Reference numbers for traceability — populated when available.
    invoice_no: Optional[str] = None     # ERP inv_nos, e.g. 'VIPL/187/27'
    so_no: Optional[str] = None          # ERP so_number, e.g. 'SO/26-27/00296'
    enquiry_no: Optional[str] = None     # ERP enquiry_no, e.g. 'CRM/26-27/EQ/0157'


class PriceRange(BaseModel):
    suggested_low: Optional[float] = None
    suggested_high: Optional[float] = None
    market_low: Optional[float] = None       # 25th percentile of market history
    market_high: Optional[float] = None      # 75th percentile
    market_median: Optional[float] = None
    sample_size: int = 0                     # # of invoices the band is based on
    unit: str = "MT"


class AnalyzeResponse(BaseModel):
    mode_used: Literal["ai", "algo"]
    price_range: PriceRange
    context_cards: List[ContextCard]
    market_signals: List[MarketSignal]
    market_history: List[HistoryRow]      # won invoices for this product
    customer_history: List[HistoryRow]    # won invoices for this customer
    inquiry_history: List[HistoryRow]     # enquiries with computed status
    reasoning: str
