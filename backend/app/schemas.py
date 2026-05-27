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
    region_id: Optional[str] = None


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
    prime_steel_rate: float
    hc_steel_rate: float
    commercial_steel_rate: float
    zinc_sgh_rate: float
    zinc_rate: float
    wire_rod_rate: float
    conv_wiping_fine_rate: float
    conv_wiping_thick_rate: float
    conv_heavy_fine_rate: float
    conv_heavy_thick_rate: float
    conv_printing_rate: float
    conv_stranding_rate: float
    loading_cost_per_mt: float = 0.0
    fuel_surcharge_pct: float = 0.0
    freight_rate_per_mt_km: float = 0.0
    rate_date: Optional[str] = None

class DailyRatesInput(BaseModel):
    prime_steel_rate: float
    hc_steel_rate: float
    commercial_steel_rate: float
    zinc_sgh_rate: float
    zinc_rate: float
    wire_rod_rate: float
    conv_wiping_fine_rate: float
    conv_wiping_thick_rate: float
    conv_heavy_fine_rate: float
    conv_heavy_thick_rate: float
    conv_printing_rate: float
    conv_stranding_rate: float
    loading_cost_per_mt: float = 0.0
    fuel_surcharge_pct: float = 0.0
    freight_rate_per_mt_km: float = 0.0


# ── Configuration Models ───────────────────────────────────────────────────

class ProductCostConfigOut(BaseModel):
    id: int
    category_id: str
    category_name: str
    size_min: Optional[float] = None
    size_max: Optional[float] = None
    gsm_kg_per_mt: Optional[float] = None
    steel_type: Optional[str] = None
    steel_weight: Optional[float] = None
    yield_loss_pct: Optional[float] = None
    min_margin_pct: Optional[float] = None
    max_margin_pct: Optional[float] = None
    conversion_process: Optional[str] = None

class ProductCostConfigInput(BaseModel):
    category_id: str
    category_name: str
    size_min: Optional[float] = None
    size_max: Optional[float] = None
    gsm_kg_per_mt: Optional[float] = None
    steel_type: Optional[str] = None
    steel_weight: Optional[float] = None
    yield_loss_pct: Optional[float] = None
    min_margin_pct: Optional[float] = None
    max_margin_pct: Optional[float] = None
    conversion_process: Optional[str] = None


# ── Analyze request/response ───────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    customer_id: int | None = None
    customer_name: str | None = None
    category_id: str
    quantity: float | None = None
    quantity_mt: float | None = None
    payment_terms: Optional[str] = "30 Days"
    mode: Literal["ai", "algo"] = "algo"   # algo by default — no API spend
    custom_params: dict | None = None
    region_id: str | None = None


class ContextCard(BaseModel):
    label: str
    value: str
    sub_text: str = ""
    icon: str = "user"
    full_width: bool = False


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
