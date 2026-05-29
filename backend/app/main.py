"""
Quote Intelligence API — Path 2 (single source of truth).
Frontend speaks only to FastAPI; FastAPI speaks only to Supabase.
"""
from __future__ import annotations
import os
from typing import List
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from app.database import (
    get_daily_rates,
    get_daily_rates_history,
    insert_daily_rates,
    list_customers,
    list_products,
    list_product_cost_configs,
    upsert_product_cost_config,
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
    ProductCostConfigOut,
    ProductCostConfigInput,
    LoginRequest,
    LoginResponse,
    UserInfo,
    UserCreate,
    UserUpdate,
    UserResponse,
)
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    verify_password,
    require_admin,
    get_password_hash,
)
from app.database import get_user_by_user_id, update_last_login, list_all_users, create_user, update_user
from datetime import timedelta


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

@app.get("/login", include_in_schema=False)
def serve_login():
    html_path = os.path.join(_STATIC_DIR, "login.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"status": "ok", "message": "Login page not found"}


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


# ── Auth Endpoints ─────────────────────────────────────────────────────────

@app.post("/api/v1/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, response: Response):
    user = get_user_by_user_id(req.user_id)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["user_id"]}, expires_delta=access_token_expires
    )
    
    update_last_login(user["user_id"])
    
    user_info = UserInfo(
        id=user["id"],
        user_id=user["user_id"],
        full_name=user["full_name"],
        role=user["role"],
        email=user.get("email"),
        feedback=user.get("feedback"),
        feedback_status=user.get("feedback_status"),
        feedback_dev_comments=user.get("feedback_dev_comments")
    )
    
    response.set_cookie(
        key="sys_access_token",
        value=access_token,
        httponly=True,
        samesite="lax"
    )
    
    return LoginResponse(access_token=access_token, user=user_info)

@app.post("/api/v1/auth/logout")
def logout(response: Response):
    response.delete_cookie(key="sys_access_token")
    return {"status": "ok", "message": "Logged out"}

class FeedbackRequest(BaseModel):
    feedback: str

@app.post("/api/v1/auth/feedback")
def submit_feedback(req: FeedbackRequest, current_user: UserInfo = Depends(get_current_user)):
    from app.database import update_user_feedback
    success = update_user_feedback(current_user.user_id, req.feedback)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save feedback")
    return {"status": "ok", "message": "Feedback saved"}

@app.get("/api/v1/auth/me", response_model=UserInfo)
def read_users_me(current_user: UserInfo = Depends(get_current_user)):
    return current_user

class ChangePasswordRequest(BaseModel):
    new_password: str

@app.put("/api/v1/auth/change-password")
def change_password(req: ChangePasswordRequest, current_user: UserInfo = Depends(get_current_user)):
    update_data = {"password": get_password_hash(req.new_password)}
    updated = update_user(current_user.user_id, update_data)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update password")
    return {"status": "ok", "message": "Password updated successfully"}

# ── Admin User Management ──────────────────────────────────────────────────

@app.get("/api/v1/admin/users", response_model=List[UserResponse])
def get_all_users(current_user: UserInfo = Depends(require_admin)):
    users = list_all_users()
    return users

@app.post("/api/v1/admin/users", response_model=UserResponse)
def add_new_user(user: UserCreate, current_user: UserInfo = Depends(require_admin)):
    existing = get_user_by_user_id(user.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="User ID already exists")
    
    hashed_password = get_password_hash(user.password)
    new_user_data = user.dict()
    new_user_data["password"] = hashed_password
    
    created = create_user(new_user_data)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return created

@app.put("/api/v1/admin/users/{user_id}", response_model=UserResponse)
def modify_user(user_id: str, updates: UserUpdate, current_user: UserInfo = Depends(require_admin)):
    existing = get_user_by_user_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
        
    update_data = updates.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
        
    updated = update_user(user_id, update_data)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update user")
    return updated

# ── Read-only Listings ─────────────────────────────────────────────────────

@app.get("/api/v1/customers", response_model=List[CustomerInfo])
def get_customers(_=Depends(get_current_user)):
    return [
        CustomerInfo(
            id=int(c["id"]),
            name=c["name"],
            total_orders=int(c.get("total_orders") or 0),
            is_repeat=bool(c.get("is_repeat")),
            region_id=c.get("region_id"),
        )
        for c in list_customers()
        if c.get("id") and c.get("name")
    ]


@app.get("/api/v1/products", response_model=List[ProductGroup])
def get_products(_=Depends(get_current_user)):
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
def get_rates(_=Depends(get_current_user)):
    return DailyRatesOut(**get_daily_rates())


@app.post("/api/v1/rates", response_model=DailyRatesOut)
def set_rates(rates: DailyRatesInput, current_user: UserInfo = Depends(get_current_user)):
    return DailyRatesOut(**insert_daily_rates(rates.model_dump(), user_id=current_user.user_id))


@app.get("/api/v1/rates/history", response_model=List[DailyRatesOut])
def get_rates_history(days: int = 7, _=Depends(get_current_user)):
    return [DailyRatesOut(**r) for r in get_daily_rates_history(days=days)]


# ── Configuration endpoints ────────────────────────────────────────────────

@app.get("/api/v1/config/product-costs", response_model=List[ProductCostConfigOut])
def get_product_costs(_=Depends(get_current_user)):
    return [ProductCostConfigOut(**c) for c in list_product_cost_configs()]


@app.post("/api/v1/config/product-costs", response_model=ProductCostConfigOut)
def update_product_cost(config: ProductCostConfigInput, current_user: UserInfo = Depends(get_current_user)):
    res = upsert_product_cost_config(config.model_dump(), user_id=current_user.user_id)
    if not res:
        raise HTTPException(status_code=500, detail="Failed to save configuration")
    return ProductCostConfigOut(**res)

@app.delete("/api/v1/config/product-costs/{category_id}")
def delete_product_cost(category_id: str, _=Depends(get_current_user)):
    from app.database import delete_product_cost_config
    if delete_product_cost_config(category_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=500, detail="Failed to delete configuration")


# ── Single bundled analyzer ────────────────────────────────────────────────

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
def analyze_quote(req: AnalyzeRequest, _=Depends(get_current_user)):
    """
    One endpoint, both modes. `mode='algo'` (default) is free; `mode='ai'` calls OpenAI.
    Returns the full bundle: prices, context, signals, three history tables, reasoning.
    """
    try:
        return analyze(req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/locations")
def get_locations(_=Depends(get_current_user)):
    """Returns all active states and corresponding cities from location_margin_config."""
    from app.database import list_location_margin_configs
    return list_location_margin_configs()
