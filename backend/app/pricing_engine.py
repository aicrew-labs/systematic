from app.schemas import QuoteRequest, QuoteResponse
from app.database import get_daily_rates, get_historical_invoices, get_historical_enquiries, CUSTOMERS
import random

def get_customer_name(customer_id: str) -> str:
    for c in CUSTOMERS:
        if str(c.get("cliid", "")) == str(customer_id):
            return c.get("cliname", "")
    return ""

def calculate_quote(request: QuoteRequest) -> QuoteResponse:
    rates = get_daily_rates()
    
    # 1. Base Cost
    # Assuming GI Wire uses MS Steel, others might use HC
    is_hc = "HC" in request.product_type.upper() or "ACSR" in request.product_type.upper()
    steel_rate = rates["steel_hc_rate"] if is_hc else rates["steel_ms_rate"]
    
    # Conversion cost (manufacturing overhead) - Mocking for now, 
    # Usually around 3000-5000 INR per MT depending on size
    conversion_cost = 4000.0
    
    # Zinc cost calculation
    # Zinc GSM (g/m^2) conversion to Kg/MT depends on wire diameter
    # Approximate formula: Zinc Consumption (Kg/MT) = (4 * GSM) / (Diameter_mm * 7.85)
    zinc_gsm = request.zinc_coating_gsm or 60.0 # Default to commercial coating
    diameter = request.diameter_mm or 2.0 # Default 2mm
    
    # Simple estimation if diameter is provided
    zinc_consumption_kg_per_mt = (4 * zinc_gsm) / (diameter * 7.85)
    zinc_cost = zinc_consumption_kg_per_mt * rates["zinc_rate"]
    
    base_cost_mt = steel_rate
    floor_price_mt = base_cost_mt + conversion_cost + zinc_cost
    
    # Target price is floor + margin (e.g. 5-8%)
    target_price_mt = floor_price_mt * 1.05
    
    # 2. Historical Data Context
    cust_name = get_customer_name(request.customer_id)
    invoices = get_historical_invoices(customer_name=cust_name, product_code=request.product_code)
    enquiries = get_historical_enquiries(customer_id=request.customer_id)
    
    historical_prices = []
    recent_quotes = []
    
    for inv in invoices[:5]: # Get last 5 invoices
        try:
            rate = float(inv.get("unit_rate", 0))
            if rate > 0:
                historical_prices.append(rate)
                recent_quotes.append({
                    "type": "Invoice",
                    "date": inv.get("order_date", ""),
                    "rate": rate,
                    "qty": float(inv.get("prod_qty", 0))
                })
        except:
            pass

    avg_historical = sum(historical_prices) / len(historical_prices) if historical_prices else None
    
    # Win rate approximation (just a dummy calculation based on enquiries vs invoices count)
    # Since status on enquiries isn't perfectly mapped, we mock a win rate
    win_rate = min(len(invoices) / max(len(enquiries), 1), 1.0) * 100 if enquiries else 0.0
    
    # 3. Market Signals & Recommendation
    # Determine recommendation based on historical + floor
    market_signal = "Neutral"
    if avg_historical and avg_historical > target_price_mt:
        recommended = avg_historical
        market_signal = "High Demand - Client historically pays well above target."
        logic = f"Client's historical average (₹{avg_historical:,.2f}) is higher than our Target Price (₹{target_price_mt:,.2f}). We recommend sticking close to their historical rate to maximize margin."
    else:
        recommended = target_price_mt
        market_signal = "Competitive Pricing Needed"
        logic = f"Target price based on today's RM rates is ₹{target_price_mt:,.2f}. Client has no strong high-price history for this item, recommending standard target."

    return QuoteResponse(
        base_cost_mt=base_cost_mt,
        zinc_cost_mt=zinc_cost,
        conversion_cost_mt=conversion_cost,
        floor_price_mt=floor_price_mt,
        target_price_mt=target_price_mt,
        recommended_price_mt=recommended,
        historical_avg_price=avg_historical,
        historical_win_rate=win_rate,
        market_signal=market_signal,
        pricing_logic_explanation=logic,
        recent_quotes=recent_quotes
    )
