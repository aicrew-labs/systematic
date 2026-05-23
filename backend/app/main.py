"""
Quote Intelligence API — Path 2 (single source of truth).
Frontend speaks only to FastAPI; FastAPI speaks only to Supabase.
"""
from __future__ import annotations
import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import (
    get_daily_rates,
    insert_daily_rates,
    list_customers,
    list_products,
)
from app.pricing_engine import analyze
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    CustomerInfo,
    DailyRatesInput,
    DailyRatesOut,
    ProductGroup,
    ProductSize,
)


app = FastAPI(
    title="Quote Intelligence API",
    description="Backend for Systematic Industries dashboard.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static dashboard ───────────────────────────────────────────────────────
# /static/* serves any asset; / serves index.html.
_HERE = os.path.dirname(__file__)
_STATIC_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "static"))
if os.path.isdir(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    html_path = os.path.join(_STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"status": "ok", "message": "Quote Intelligence API — dashboard not found in /static"}


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "Quote Intelligence", "version": "2.0.0"}


@app.get("/api/v1/_diagnose", include_in_schema=False)
def diagnose():
    """
    Temporary endpoint for debugging Railway connectivity.
    Returns whether Supabase env vars are present and whether a trivial
    query succeeds. Safe to call: returns no row data.
    """
    import os
    from app.database import supabase

    info: dict = {
        "has_url":     bool(os.getenv("SUPABASE_URL")),
        "url_prefix":  (os.getenv("SUPABASE_URL") or "")[:30],
        "has_key":     bool(os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")),
        "key_length":  len(os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""),
        "client_init": supabase is not None,
    }
    if supabase is None:
        info["error"] = "Supabase client failed to initialise"
        return info
    try:
        res = supabase.table("customers").select("id").limit(1).execute()
        info["query_ok"]   = True
        info["row_count"]  = len(res.data or [])
    except Exception as e:
        info["query_ok"]    = False
        info["error_type"]  = type(e).__name__
        info["error_msg"]   = str(e)[:300]
    return info


# ── Read-only listings ─────────────────────────────────────────────────────

@app.get("/api/v1/customers", response_model=List[CustomerInfo])
def get_customers():
    return [
        CustomerInfo(
            id=int(c["id"]),
            name=c["name"],
            total_orders=int(c.get("total_orders") or 0),
            is_repeat=bool(c.get("is_repeat")),
        )
        for c in list_customers()
        if c.get("id") and c.get("name")
    ]


@app.get("/api/v1/products", response_model=List[ProductGroup])
def get_products():
    """Returns products grouped by product_type for the UI dropdown."""
    grouped: dict[str, list[ProductSize]] = {}
    for p in list_products():
        ptype = (p.get("product_type") or "").strip() or "Other"
        grouped.setdefault(ptype, []).append(ProductSize(
            id=int(p["id"]),
            size_label=p.get("size_label") or "—",
            size_mm=p.get("size_mm"),
            unit_of_measure=p.get("unit_of_measure") or "MT",
        ))
    return [ProductGroup(product_type=t, sizes=sizes)
            for t, sizes in sorted(grouped.items())]


@app.get("/api/v1/rates", response_model=DailyRatesOut)
def get_rates():
    return DailyRatesOut(**get_daily_rates())


@app.post("/api/v1/rates", response_model=DailyRatesOut)
def set_rates(rates: DailyRatesInput):
    return DailyRatesOut(**insert_daily_rates(rates.model_dump()))


# ── Single bundled analyzer ────────────────────────────────────────────────

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
def analyze_quote(req: AnalyzeRequest):
    """
    One endpoint, both modes. `mode='algo'` (default) is free; `mode='ai'` calls OpenAI.
    Returns the full bundle: prices, context, signals, three history tables, reasoning.
    """
    try:
        return analyze(req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
