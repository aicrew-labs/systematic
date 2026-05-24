"""
Pricing engine — purely history-driven.

The four ops-data tiles (FG stock, machine utilisation, dispatch ETA, RM cost)
are intentionally returned as 'N/A' until backing data is wired up. We don't
display numbers we can't justify.

Recommendation model:
  1. Market band: P25 / median / P75 of won invoices for this product
     (last 90 days; widen to all-time if <3 samples).
  2. Customer profile drives the anchor:
     - bought this exact product before → anchor to their last-5 avg
     - repeat customer (different product) → market median with loyalty tilt
     - new customer → upper market band (premium)
  3. Enquiry-signal tilt: ±2% if recent enquiries cluster above/below market.
  4. Payment-terms premium: percentage scales with credit days.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Iterable

from app.aerial_engine import AerialEngine
from app.database import (
    enquiries_for_product,
    get_customer,
    get_product,
    invoice_lookup_for_product,
    invoices_for_customer,
    invoices_for_product,
    sales_order_lookup_for_product,
    get_daily_rates,
    get_product_cost_config,
    get_location_margin_config,
)
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ContextCard,
    HistoryRow,
    MarketSignal,
    PriceRange,
)


# Payment-terms premium as a percentage of the suggested price.
# ~12% annualized cost-of-capital pro-rated to credit days, plus a risk premium.
PAYMENT_PREMIUM = {
    "Advance":  -0.010,   # 1% reward — money in immediately
    "7 Days":    0.000,
    "30 Days":   0.010,
    "45 Days":   0.018,
    "60 Days":   0.025,
    "90 Days":   0.040,
    "120 Days":  0.055,
}

RECENT_DAYS = 90


# ── Helpers ───────────────────────────────────────────────────────────────

def _fmt_date(value) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _percentile(sorted_values: list[float], pct: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (k - lo)


def _parse_iso(s) -> date | None:
    if not s:
        return None
    if isinstance(s, date):
        return s
    try:
        return datetime.fromisoformat(str(s)[:10]).date()
    except Exception:
        return None


def _enquiry_status(
    enq_status: str | None,
    customer_id: int | None,
    won_lookup: dict[int, dict],
    so_lookup: dict[int, dict],
) -> str:
    if customer_id and customer_id in won_lookup:
        return "won"
    if customer_id and customer_id in so_lookup:
        return "in_progress"
    s = (enq_status or "").strip().upper()
    if not s:
        return "open"
    if "LOST" in s or "CANCEL" in s or "CLOSE" in s:
        return "lost"
    return "open"


def _to_history(invoices: Iterable[dict], outcome: str = "won") -> list[HistoryRow]:
    rows: list[HistoryRow] = []
    for inv in invoices:
        qty    = float(inv.get("quantity")  or 0)
        stored = float(inv.get("unit_rate") or 0)
        # Always trust unit_rate. Fall back to prod_total / qty (line subtotal
        # before tax) only if unit_rate is missing. Never use total_amount.
        if stored > 0:
            rate = stored
        elif qty > 0:
            line_total = float(inv.get("prod_total") or 0)
            rate = (line_total / qty) if line_total > 0 else 0
        else:
            rate = 0
        rows.append(HistoryRow(
            date=_fmt_date(inv.get("invoice_date")),
            customer_name=inv.get("customer_name"),
            product_label=inv.get("prod_code"),
            rate=round(rate, 2) if rate else None,
            quantity=qty if qty else None,
            unit=inv.get("unit"),
            outcome=outcome,  # type: ignore[arg-type]
            invoice_no=inv.get("erp_inv_nos"),
            so_no=inv.get("erp_so_no"),
        ))
    return rows


def _rate_of(inv: dict) -> float:
    """Same trustworthy rate logic as _to_history but as a scalar."""
    stored = float(inv.get("unit_rate") or 0)
    if stored > 0:
        return stored
    qty = float(inv.get("quantity") or 0)
    line_total = float(inv.get("prod_total") or 0)
    if qty > 0 and line_total > 0:
        return line_total / qty
    return 0


# ── Main entry point ──────────────────────────────────────────────────────

def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    customer = get_customer(req.customer_id)
    product  = get_product(req.product_id)
    if not customer:
        raise ValueError(f"Customer {req.customer_id} not found")
    if not product:
        raise ValueError(f"Product {req.product_id} not found")

    p_label = f"{product.get('product_type')} {product.get('size_label')}"
    unit = product.get("unit_of_measure") or "MT"

    # ── 1. Pull history ─────────────────────────────────────────────────────
    market_inv = invoices_for_product(req.product_id, limit=200)
    cust_inv   = invoices_for_customer(req.customer_id, limit=200)
    enquiries  = enquiries_for_product(req.product_id, limit=100)
    won_lookup = invoice_lookup_for_product(req.product_id)
    so_lookup  = sales_order_lookup_for_product(req.product_id)

    today = date.today()
    cutoff = today - timedelta(days=RECENT_DAYS)

    # ── 2. Compute Floor Cost ──────────────────────────────────────────────
    cat_code = product.get("cost_category_code") if product else None
    config = get_product_cost_config(cat_code) if cat_code else None
    rates = get_daily_rates()
    
    floor_val = "N/A"
    floor_sub = "Configuration missing or inactive"
    floor_price = None
    
    if config:
        msRate = float(rates.get("ms_steel_rate", 0))
        hcRate = float(rates.get("hc_steel_rate", 0))
        zincRate = float(rates.get("zinc_rate", 0))
        
        steel_rate = hcRate if config.get("steel_type") == "HC" else msRate
        steel_cost = (steel_rate / 1000) * float(config.get("steel_weight_per_mt") or 0)
        zinc_cost = zincRate * float(config.get("zinc_weight_per_mt") or 0)
        yield_loss_pct = float(config.get("yield_loss_pct") or 0)
        yield_loss_mult = 1 + (yield_loss_pct / 100)
        conv_cost = float(config.get("conversion_cost_per_mt") or 0)
        packing_cost = float(config.get("packing_cost_per_mt") or 0)
        
        floor_price = (steel_cost + zinc_cost) * yield_loss_mult + conv_cost + packing_cost
        floor_val = f"₹{floor_price:,.2f}"
        
        steel_disp = f"Steel: ₹{steel_cost:,.0f}"
        zinc_disp = f"Zinc: ₹{zinc_cost:,.0f}" if zinc_cost > 0 else ""
        yl_disp = f"Yield: {yield_loss_pct}%" if yield_loss_pct > 0 else ""
        conv_disp = f"Conv: ₹{conv_cost:,.0f}"
        pack_disp = f"Pack: ₹{packing_cost:,.0f}" if packing_cost > 0 else ""
        
        parts = [p for p in [steel_disp, zinc_disp, yl_disp, conv_disp, pack_disp] if p]
        floor_sub = ", ".join(parts) + " (excl. tax & freight)"

    # ── 3. Market band ──────────────────────────────────────────────────────
    recent_market = [i for i in market_inv if (_parse_iso(i.get("invoice_date")) or today) >= cutoff]
    sample = recent_market if len(recent_market) >= 3 else market_inv
    market_rates = sorted(r for r in (_rate_of(i) for i in sample) if r > 0)

    if market_rates:
        market_low    = _percentile(market_rates, 0.25)
        market_high   = _percentile(market_rates, 0.75)
        market_median = _percentile(market_rates, 0.50)
    else:
        market_low = market_high = market_median = None

    # ── 4. Customer profile & Adjustments ───────────────────────────────────
    cust_inv_this = [i for i in cust_inv if i.get("product_id") == req.product_id]
    cust_rates_this = [_rate_of(i) for i in cust_inv_this[:5] if _rate_of(i) > 0]
    customer_avg = (sum(cust_rates_this) / len(cust_rates_this)) if cust_rates_this else None

    is_repeat = bool(customer.get("is_repeat")) or int(customer.get("total_orders") or 0) > 0
    past_orders = int(customer.get("total_orders") or 0)

    if customer_avg:
        profile = "repeat_known_product"
    elif is_repeat:
        profile = "repeat_new_product"
    else:
        profile = "new_customer"

    # Profile Adjustment (Competitive Tilt)
    profile_adj = 0.0
    pct_diff = 0.0
    competitiveness_source = None
    comp_product = None
    comp_rate = 0.0
    comp_median = 0.0
    comp_peers = 0
    comp_date = ""

    if cust_inv:
        # Search recent invoices to find one with same-day market peers
        for inv in cust_inv[:15]:
            inv_date = _parse_iso(inv.get("invoice_date"))
            if not inv_date:
                continue
            inv_date_str = inv.get("invoice_date")[:10]
            inv_prod_id = inv.get("product_id")
            inv_rate = _rate_of(inv)
            if inv_rate <= 0:
                continue
                
            # Use pre-fetched market_inv if same product, otherwise fetch
            peer_invs = market_inv if inv_prod_id == req.product_id else invoices_for_product(inv_prod_id, limit=200)
            
            # Filter to exactly the same day, EXCLUDING this customer's own invoices
            same_day_peers = [
                p for p in peer_invs
                if p.get("invoice_date", "").startswith(inv_date_str)
                and p.get("customer_id") != req.customer_id
            ]
            peer_rates = sorted(r for r in (_rate_of(p) for p in same_day_peers) if r > 0)
            
            # Need at least 1 other customer's invoice to form a comparison
            if len(peer_rates) >= 1:
                day_median = _percentile(peer_rates, 0.50)
                if day_median and day_median > 0:
                    pct_diff = ((inv_rate - day_median) / day_median) * 100
                    competitiveness_source = "this product" if inv_prod_id == req.product_id else "other products"
                    
                    comp_product = inv.get("prod_code", "Unknown Product")
                    comp_rate = inv_rate
                    comp_median = day_median
                    comp_peers = len(peer_rates)
                    comp_date = inv_date_str
                    break

    # Apply tilt if we found a comparison
    if competitiveness_source:
        # Adjustment is proportional to the variance, capped at ±5.0%
        profile_adj = round(max(-5.0, min(5.0, pct_diff)), 1)

    # Location Adjustment
    loc_adj = 0.0
    region_id = customer.get("region_id")
    if region_id:
        loc_config = get_location_margin_config(region_id)
        if loc_config:
            loc_adj = float(loc_config.get("margin_adjustment_pct") or 0.0)

    # ── 5. Calculate Final Cost-Plus Price ──────────────────────────────────
    pp = PAYMENT_PREMIUM.get(req.payment_terms or "30 Days", 0.01) * 100  # Convert to % for margin add

    sug_low = sug_high = None
    base_min = 0.0
    base_max = 0.0
    final_min_margin = 0.0
    final_max_margin = 0.0

    if floor_price and config:
        base_min = float(config.get("min_margin_pct") or 5.0)
        base_max = float(config.get("max_margin_pct") or 10.0)
        
        final_min_margin = base_min + loc_adj + profile_adj + pp
        final_max_margin = base_max + loc_adj + profile_adj + pp
        
        # Enforce hard floor: margin cannot drop below 0%
        final_min_margin = max(0.0, final_min_margin)
        final_max_margin = max(final_min_margin + 0.1, final_max_margin)
        
        sug_low = round(floor_price * (1 + final_min_margin / 100), 2)
        sug_high = round(floor_price * (1 + final_max_margin / 100), 2)

    price_range = PriceRange(
        suggested_low=sug_low,
        suggested_high=sug_high,
        market_low=round(market_low, 2)       if market_low       else None,
        market_high=round(market_high, 2)     if market_high      else None,
        market_median=round(market_median, 2) if market_median    else None,
        sample_size=len(market_rates),
        unit=unit,
    )

    # ── 6. Context cards ────────────────────────────────────────────────────
    cust_inv_count = len(cust_inv)
    cust_inv_this_count = len(cust_inv_this)
    cards = [
        ContextCard(
            label="Customer",
            value=("Repeat — known product" if profile == "repeat_known_product"
                   else "Repeat — new product" if profile == "repeat_new_product"
                   else "New Customer"),
            sub_text=(f"{past_orders} past order(s) · {cust_inv_this_count} on this product"
                      if past_orders else "First-time enquiry"),
        ),
        ContextCard(
            label="PRODUCT FLOOR COST",
            value=floor_val,
            sub_text=floor_sub,
        ),
        ContextCard(
            label="FG Stock",
            value="N/A",
            sub_text="Awaiting source data",
        ),
        ContextCard(
            label="Machine Util.",
            value="N/A",
            sub_text="Awaiting source data",
        ),
        ContextCard(
            label="Est. Dispatch",
            value="N/A",
            sub_text="Awaiting source data",
        ),
    ]

    # ── 7. Market signals ───────────────────────────────────────────────────
    signals: list[MarketSignal] = []

    # Show margin breakdown
    if config:
        signals.append(MarketSignal(
            color="blue",
            text=f"Base Margin: {base_min:.1f}% - {base_max:.1f}% (from config '{cat_code}')",
        ))
    if loc_adj != 0:
        sign = "+" if loc_adj > 0 else ""
        signals.append(MarketSignal(
            color="amber" if loc_adj < 0 else "blue",
            text=f"Location Adj: {sign}{loc_adj}% applied for region '{region_id}'",
        ))
    if profile_adj != 0:
        sign = "+" if profile_adj > 0 else ""
        c_name = customer.get("name", "Customer")
        signals.append(MarketSignal(
            color="amber" if profile_adj < 0 else "blue",
            text=f"Profile Adj: {sign}{profile_adj}% (On {comp_date}, {c_name} bought {comp_product} @ ₹{comp_rate:,.0f}/{unit}. Same-day market median of {comp_peers} customers was ₹{comp_median:,.0f}/{unit}. Variance: {pct_diff:+.1f}%)",
        ))
    if pp != 0:
        sign = "+" if pp > 0 else ""
        signals.append(MarketSignal(
            color="blue",
            text=f"Payment Terms Premium: {sign}{pp:.1f}% applied for '{req.payment_terms}'",
        ))

    c_name = customer.get("name", "Customer")
    if customer_avg:
        # Repeat customer who has bought this product before
        last_this = cust_inv_this[0] if cust_inv_this else None
        if last_this:
            last_date = last_this.get("invoice_date", "")[:10]
            last_rate_this = _rate_of(last_this)
            signals.append(MarketSignal(
                color="green",
                text=f"Last purchase: {c_name} bought {p_label} on {last_date} @ ₹{last_rate_this:,.0f}/{unit} ({cust_inv_this_count} purchase(s) total, avg ₹{customer_avg:,.0f})",
            ))
            # Check same-day peers for this product — EXCLUDE this customer's own invoices
            same_day = [
                p for p in market_inv
                if p.get("invoice_date", "").startswith(last_date)
                and p.get("customer_id") != req.customer_id
            ]
            same_day_rates = sorted(r for r in (_rate_of(p) for p in same_day) if r > 0)
            if len(same_day_rates) >= 1:
                sd_avg = sum(same_day_rates) / len(same_day_rates)
                sd_median = _percentile(same_day_rates, 0.50)
                diff_pct = ((last_rate_this - sd_median) / sd_median * 100) if sd_median else 0
                color = "amber" if diff_pct < -2 else "blue" if diff_pct > 2 else "green"
                signals.append(MarketSignal(
                    color=color,
                    text=f"Same-day market ({last_date}): {len(same_day_rates)} other customer(s) bought {p_label} — avg ₹{sd_avg:,.0f}, median ₹{sd_median:,.0f}/{unit}. {c_name} paid {diff_pct:+.1f}% vs that day's median.",
                ))
            else:
                signals.append(MarketSignal(
                    color="blue",
                    text=f"Same-day market ({last_date}): No other customers bought {p_label} on that day — no same-day comparison available.",
                ))
    elif is_repeat and cust_inv:
        # Repeat customer but hasn't bought this product — show their last invoice on any product
        last_inv = cust_inv[0]
        last_prod_code = last_inv.get("prod_code", "Unknown")
        last_inv_date = last_inv.get("invoice_date", "")[:10]
        last_inv_rate = _rate_of(last_inv)
        last_prod_id = last_inv.get("product_id")
        signals.append(MarketSignal(
            color="blue",
            text=f"Last purchase: {c_name} bought {last_prod_code} on {last_inv_date} @ ₹{last_inv_rate:,.0f}/{unit} — has not bought {p_label} before ({past_orders} total order(s)).",
        ))
        # Same-day comparison for that other product — EXCLUDE this customer's own invoices
        if last_prod_id and last_inv_rate > 0:
            peer_invs_other = invoices_for_product(last_prod_id, limit=200)
            same_day_other = [
                p for p in peer_invs_other
                if p.get("invoice_date", "").startswith(last_inv_date)
                and p.get("customer_id") != req.customer_id
            ]
            sd_other_rates = sorted(r for r in (_rate_of(p) for p in same_day_other) if r > 0)
            if len(sd_other_rates) >= 1:
                sd_other_median = _percentile(sd_other_rates, 0.50)
                diff_pct = ((last_inv_rate - sd_other_median) / sd_other_median * 100) if sd_other_median else 0
                color = "amber" if diff_pct < -2 else "blue" if diff_pct > 2 else "green"
                signals.append(MarketSignal(
                    color=color,
                    text=f"Same-day market ({last_inv_date}): {len(sd_other_rates)} other customer(s) bought {last_prod_code} — median ₹{sd_other_median:,.0f}/{unit}. {c_name} paid {diff_pct:+.1f}% vs that day's median. Profile tilt applied to margin.",
                ))
            else:
                signals.append(MarketSignal(
                    color="blue",
                    text=f"Same-day market ({last_inv_date}): No other customers bought {last_prod_code} on that day — profile tilt not applicable.",
                ))
    else:
        signals.append(MarketSignal(
            color="amber",
            text=f"New customer — no prior order history. Standard base margin applied.",
        ))

    lost_count = sum(1 for e in enquiries
                     if (e.get("customer_id") == req.customer_id)
                     and _enquiry_status(e.get("status"), e.get("customer_id"), won_lookup, so_lookup) == "lost")
    if lost_count > 0:
        signals.append(MarketSignal(
            color="red",
            text=f"This customer has {lost_count} lost enquiry on this product — they're price-sensitive",
        ))

    # ── 8. History tables ───────────────────────────────────────────────────
    market_history   = _to_history(market_inv, "won")
    customer_history = _to_history(cust_inv,   "won")
    inquiry_history: list[HistoryRow] = []
    for e in enquiries:
        cid = e.get("customer_id")
        outcome = _enquiry_status(e.get("status"), cid, won_lookup, so_lookup)
        ref_inv = won_lookup.get(cid) if cid and outcome == "won" else None
        ref_so  = so_lookup.get(cid)  if cid and outcome == "in_progress" else None
        inquiry_history.append(HistoryRow(
            date=_fmt_date(e.get("enquiry_date")),
            customer_name=e.get("customer_name"),
            product_label=e.get("product_desc"),
            rate=float(e["price_offered"]) if e.get("price_offered") else None,
            quantity=float(e["quantity"]) if e.get("quantity") else None,
            unit=e.get("unit"),
            outcome=outcome,  # type: ignore[arg-type]
            enquiry_no=e.get("erp_id"),
            invoice_no=ref_inv.get("invoice_no") if ref_inv else None,
            so_no=(ref_inv.get("so_no") if ref_inv else (ref_so.get("so_no") if ref_so else None)),
        ))

    # ── 9. Reasoning ────────────────────────────────────────────────────────
    if req.mode == "ai":
        reasoning = _ai_reasoning(req, customer, product, customer_avg, market_median,
                                  sug_low, sug_high)
    else:
        reasoning = _algo_reasoning(req, customer, product, profile, customer_avg,
                                    market_low, market_median, market_high,
                                    sug_low, sug_high, len(market_rates),
                                    loc_adj, profile_adj, pp, lost_count, base_min, base_max)

    return AnalyzeResponse(
        mode_used=req.mode,
        price_range=price_range,
        context_cards=cards,
        market_signals=signals,
        market_history=market_history,
        customer_history=customer_history,
        inquiry_history=inquiry_history,
        reasoning=reasoning,
    )


# ── Reasoning generators ──────────────────────────────────────────────────

def _algo_reasoning(req, customer, product, profile, customer_avg,
                    market_low, market_median, market_high,
                    sug_low, sug_high, sample_size,
                    loc_adj, profile_adj, pp, lost_count, base_min, base_max) -> str:
    name = customer.get("name", "Customer")
    p_label = f"{product.get('product_type')} {product.get('size_label')}"
    unit = product.get("unit_of_measure") or "MT"

    parts: list[str] = []

    # Profile
    if profile == "repeat_known_product":
        parts.append(f"{name} has bought {p_label} before — historical avg ₹{customer_avg:,.0f}/{unit}.")
    elif profile == "repeat_new_product":
        parts.append(f"{name} is a known customer but has not bought {p_label} before.")
    elif profile == "new_customer":
        parts.append(f"{name} is a new customer.")

    # Base Margin + Adjustments
    if base_min > 0:
        parts.append(f"Base margin applied: {base_min:.1f}% to {base_max:.1f}%.")
        
        if loc_adj != 0:
            sign = "+" if loc_adj > 0 else ""
            parts.append(f"Region '{customer.get('region_id')}' adds {sign}{loc_adj}%.")
            
        if profile_adj != 0:
            sign = "+" if profile_adj > 0 else ""
            parts.append(f"Historical competitiveness tilt adds {sign}{profile_adj}%.")

    # Payment terms
    if pp != 0:
        sign = "+" if pp > 0 else ""
        parts.append(f"'{req.payment_terms}' adds {sign}{pp:.1f}%.")

    # Final
    if sug_low and sug_high:
        parts.append(f"Recommended quote: ₹{int(sug_low):,} – ₹{int(sug_high):,}/{unit}.")

    return " ".join(parts)


def _ai_reasoning(req, customer, product, customer_avg, market_median, sug_low, sug_high) -> str:
    is_repeat = bool(customer.get("is_repeat")) or int(customer.get("total_orders") or 0) > 0
    target = ((sug_low or 0) + (sug_high or 0)) / 2 if (sug_low and sug_high) else 0
    return AerialEngine.generate_reasoning(
        request_data={
            "product_type": product.get("product_type", ""),
            "product_code": product.get("size_label", ""),
        },
        math_context={
            "floor_price_mt":       0,    # unused — no RM cost baseline
            "target_price_mt":      target,
            "historical_avg_price": customer_avg or market_median,
        },
        customer_stats={
            "name":         customer.get("name", ""),
            "is_repeat":    is_repeat,
            "total_orders": int(customer.get("total_orders") or 0),
        },
    )
