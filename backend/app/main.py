from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import os

from app.schemas import CustomerInfo, ProductInfo, DailyRatesInput, QuoteRequest, QuoteResponse
from app.database import get_customers, get_products, get_daily_rates, update_daily_rates
from app.pricing_engine import calculate_quote

app = FastAPI(
    title="Systematic Quote Intelligence API",
    description="Backend API for real-time GI Wire pricing, utilizing ERP data.",
    version="1.0.0"
)

# CORS — allow Railway frontend domain + local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve static HTML dashboard ─────────────────────────────────────────────
# In production (Railway) the HTML lives one level up from backend/
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serve the Quote Intelligence dashboard HTML."""
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"status": "ok", "message": "Quote Intelligence API — dashboard not found in /static"}

# ── API routes ───────────────────────────────────────────────────────────────

@app.get("/health")
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
