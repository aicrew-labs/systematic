from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from app.schemas import CustomerInfo, ProductInfo, DailyRatesInput, QuoteRequest, QuoteResponse
from app.database import get_customers, get_products, get_daily_rates, update_daily_rates
from app.pricing_engine import calculate_quote

app = FastAPI(
    title="Systematic Quote Intelligence API",
    description="Backend API for real-time GI Wire pricing, utilizing ERP data.",
    version="1.0.0"
)

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Quote Intelligence Backend is running!"}

@app.get("/api/v1/customers", response_model=List[CustomerInfo])
def get_all_customers():
    """Returns the list of customers loaded from the ERP JSON data."""
    return get_customers()

@app.get("/api/v1/products", response_model=List[ProductInfo])
def get_all_products():
    """Returns the list of products (derived from RMS specs)."""
    return get_products()

@app.get("/api/v1/rates")
def get_current_rates():
    """Get the current daily raw material rates."""
    return get_daily_rates()

@app.post("/api/v1/rates")
def set_daily_rates(rates: DailyRatesInput):
    """Admin endpoint to update the daily RM rates."""
    updated = update_daily_rates(rates.model_dump())
    return {"status": "success", "rates": updated}

@app.post("/api/v1/analyze", response_model=QuoteResponse)
def analyze_quote(request: QuoteRequest):
    """
    The core Quote Intelligence engine.
    Calculates costs, historical context, and provides pricing recommendations.
    """
    return calculate_quote(request)
