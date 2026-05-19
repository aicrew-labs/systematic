from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CustomerInfo(BaseModel):
    customer_id: str
    name: str

class ProductInfo(BaseModel):
    product_code: str
    category: str
    diameter_mm: Optional[float] = None
    tensile_strength: Optional[str] = None
    zinc_coating_gsm: Optional[float] = None

class DailyRatesInput(BaseModel):
    steel_ms_rate: float
    steel_hc_rate: float
    zinc_rate: float

class QuoteRequest(BaseModel):
    customer_id: str
    customer_name: Optional[str] = None
    product_type: str
    product_code: str
    quantity_mt: float
    diameter_mm: Optional[float] = None
    zinc_coating_gsm: Optional[float] = None
    tensile_strength: Optional[str] = None
    application: Optional[str] = None
    location: Optional[str] = None
    payment_terms: Optional[str] = None

class QuoteResponse(BaseModel):
    base_cost_mt: float
    zinc_cost_mt: float
    conversion_cost_mt: float
    floor_price_mt: float
    target_price_mt: float
    recommended_price_mt: float
    historical_avg_price: Optional[float] = None
    historical_win_rate: Optional[float] = None
    market_signal: str
    pricing_logic_explanation: str
    recent_quotes: List[Dict[str, Any]] = []
