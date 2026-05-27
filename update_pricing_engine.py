
with open('backend/app/pricing_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_content = ''.join(lines[:150])

# Write the rest
rest = '''
# ── Main entry point ──────────────────────────────────────────────────────

def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    customer = get_customer(req.customer_id) if req.customer_id else {}
    if not customer and req.customer_id:
        raise ValueError(f"Customer {req.customer_id} not found")

    is_custom = (req.category_id == "Custom")
    if is_custom:
        config = req.custom_params or {}
        p_label = "Custom Product"
        market_inv = []
    else:
        config = get_product_cost_config(req.category_id)
        p_label = config.get('category_name') if config else req.category_id
        market_inv = invoices_for_category(req.category_id, limit=200)

    unit = "MT"

    # ── 1. Pull history ─────────────────────────────────────────────────────
    cust_inv   = invoices_for_customer(req.customer_id, limit=200) if req.customer_id else []
    enquiries  = []
    won_lookup = {}
    so_lookup  = {}

    today = date.today()
    cutoff = today - timedelta(days=RECENT_DAYS)

    # ── 2. Compute Floor Cost ──────────────────────────────────────────────
    rates = get_daily_rates()
    
    floor_val = "N/A"
    floor_sub = "Configuration missing or inactive"
    floor_price = None
    
    if config:
        # Step 3: Steel Cost
        primeRate = float(rates.get("prime_steel_rate", 0))
        hcRate = float(rates.get("hc_steel_rate", 0))
        commRate = float(rates.get("commercial_steel_rate", 0))
        
        st_type = str(config.get("steel_type") or "").upper()
        if "HC" in st_type:
            steel_rate = hcRate
        elif "COMMERCIAL" in st_type:
            steel_rate = commRate
        else:
            steel_rate = primeRate
            
        steel_cost = (steel_rate / 1000) * float(config.get("steel_weight") or (1000.0 if is_custom else 0))

        # Step 1 & 2: Zinc Cost
        if is_custom:
            size = float(config.get("size_mm") or 1.0)
        else:
            size_min = float(config.get("size_min") or 0)
            size = size_min if size_min > 0 else 1.0
            
        gsm = float(config.get("gsm_kg_per_mt") or config.get("gsm") or 0)
        yield_loss_pct = float(config.get("yield_loss_pct") or (25.0 if is_custom else 0))
        yield_loss_mult = 1 + (yield_loss_pct / 100)
        
        zinc_weight = ((gsm / size) * 0.51) * yield_loss_mult
        zincRate = float(rates.get("zinc_sgh_rate", rates.get("zinc_rate", 0)))
        zinc_cost = zinc_weight * zincRate
        
        # Step 4: Conversion Cost
        conv_proc = str(config.get("conversion_process") or "").lower()
        if "wiping fine" in conv_proc:
            conv_cost = float(rates.get("conv_wiping_fine_rate", 0))
        elif "wiping thick" in conv_proc:
            conv_cost = float(rates.get("conv_wiping_thick_rate", 0))
        elif "heavy fine" in conv_proc:
            conv_cost = float(rates.get("conv_heavy_fine_rate", 0))
        elif "heavy thick" in conv_proc:
            conv_cost = float(rates.get("conv_heavy_thick_rate", 0))
        elif "printing" in conv_proc:
            conv_cost = float(rates.get("conv_printing_rate", 0))
        elif "stranding" in conv_proc:
            conv_cost = float(rates.get("conv_stranding_rate", 0))
        else:
            conv_cost = 0.0
            
        # Step 5: Floor Price
        floor_price = steel_cost + zinc_cost + conv_cost
        floor_val = f"₹{floor_price:,.2f}"
        
        steel_disp = f"Steel: ₹{steel_cost:,.0f}"
        zinc_disp = f"Zinc: ₹{zinc_cost:,.0f}" if zinc_cost > 0 else ""
        conv_disp = f"Conv: ₹{conv_cost:,.0f}"
        
        parts = [p for p in [steel_disp, zinc_disp, conv_disp] if p]
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
    cust_inv_this = [i for i in cust_inv if i.get("cost_category_code") == req.category_id]
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

    if cust_inv and not is_custom:
        for inv in cust_inv[:15]:
            inv_date = _parse_iso(inv.get("invoice_date"))
            if not inv_date:
                continue
            inv_date_str = inv.get("invoice_date")[:10]
            inv_cat_id = inv.get("cost_category_code")
            inv_rate = _rate_of(inv)
            if inv_rate <= 0:
                continue
                
            peer_invs = market_inv if inv_cat_id == req.category_id else invoices_for_category(inv_cat_id, limit=200) if inv_cat_id else []
            
            same_day_peers = [
                p for p in peer_invs
                if p.get("invoice_date", "").startswith(inv_date_str)
                and p.get("customer_id") != req.customer_id
            ]
            peer_rates = sorted(r for r in (_rate_of(p) for p in same_day_peers) if r > 0)
            
            if len(peer_rates) >= 1:
                day_median = _percentile(peer_rates, 0.50)
                if day_median and day_median > 0:
                    pct_diff = ((inv_rate - day_median) / day_median) * 100
                    competitiveness_source = "this product" if inv_cat_id == req.category_id else "other products"
                    
                    comp_product = inv.get("prod_code", "Unknown Product")
                    comp_rate = inv_rate
                    comp_median = day_median
                    comp_peers = len(peer_rates)
                    comp_date = inv_date_str
                    break

    if competitiveness_source:
        profile_adj = round(max(-5.0, min(5.0, pct_diff)), 1)

    loc_adj = 0.0
    region_id = customer.get("region_id")
    if region_id:
        loc_config = get_location_margin_config(region_id)
        if loc_config:
            loc_adj = float(loc_config.get("margin_adjustment_pct") or 0.0)

    # ── 5. Calculate Final Cost-Plus Price ──────────────────────────────────
    pp = PAYMENT_PREMIUM.get(req.payment_terms or "30 Days", 0.01) * 100

    sug_low = sug_high = None
    base_min = 0.0
    base_max = 0.0
    final_min_margin = 0.0
    final_max_margin = 0.0

    if floor_price and config and not is_custom:
        base_min = float(config.get("min_margin_pct") or 5.0)
        base_max = float(config.get("max_margin_pct") or 10.0)
        
        final_min_margin = base_min + loc_adj + profile_adj + pp
        final_max_margin = base_max + loc_adj + profile_adj + pp
        
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
            value=("Repeat — known category" if profile == "repeat_known_product"
                   else "Repeat — new category" if profile == "repeat_new_product"
                   else "New Customer"),
            sub_text=(f"{past_orders} past order(s) · {cust_inv_this_count} in this category"
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

    if config and not is_custom:
        signals.append(MarketSignal(
            color="blue",
            text=f"Base Margin: {base_min:.1f}% - {base_max:.1f}% (from config '{req.category_id}')",
        ))
    if loc_adj != 0:
        sign = "+" if loc_adj > 0 else ""
        signals.append(MarketSignal(
            color="amber" if loc_adj < 0 else "blue",
            text=f"Location Adj: {sign}{loc_adj}% applied for region '{region_id}'",
        ))
    if profile_adj != 0:
        sign = "+" if profile_adj > 0 else ""
        c_name = customer.get("name", req.customer_name or "Customer")
        signals.append(MarketSignal(
            color="amber" if profile_adj < 0 else "blue",
            text=f"Profile Adj: {sign}{profile_adj}% (On {comp_date}, {c_name} bought {comp_product} @ ₹{comp_rate:,.0f}/{unit}. Variance: {pct_diff:+.1f}% vs median)",
        ))
    if pp != 0:
        sign = "+" if pp > 0 else ""
        signals.append(MarketSignal(
            color="blue",
            text=f"Payment Terms Premium: {sign}{pp:.1f}% applied for '{req.payment_terms}'",
        ))

    c_name = customer.get("name", req.customer_name or "Customer")
    if customer_avg:
        last_this = cust_inv_this[0] if cust_inv_this else None
        if last_this:
            last_date = last_this.get("invoice_date", "")[:10]
            last_rate_this = _rate_of(last_this)
            signals.append(MarketSignal(
                color="green",
                text=f"Last purchase: {c_name} bought {p_label} on {last_date} @ ₹{last_rate_this:,.0f}/{unit} ({cust_inv_this_count} purchase(s) total, avg ₹{customer_avg:,.0f})",
            ))
    elif is_repeat and cust_inv:
        last_inv = cust_inv[0]
        last_prod_code = last_inv.get("prod_code", "Unknown")
        last_inv_date = last_inv.get("invoice_date", "")[:10]
        last_inv_rate = _rate_of(last_inv)
        signals.append(MarketSignal(
            color="blue",
            text=f"Last purchase: {c_name} bought {last_prod_code} on {last_inv_date} @ ₹{last_inv_rate:,.0f}/{unit} — has not bought {p_label} before.",
        ))
    else:
        signals.append(MarketSignal(
            color="amber",
            text=f"New customer — no prior order history.",
        ))

    market_history   = _to_history(market_inv, "won")
    customer_history = _to_history(cust_inv,   "won")
    inquiry_history: list[HistoryRow] = []

    if req.mode == "ai":
        reasoning = _ai_reasoning(req, customer, p_label, customer_avg, market_median, sug_low, sug_high)
    else:
        reasoning = _algo_reasoning(req, customer, p_label, profile, customer_avg,
                                    market_low, market_median, market_high,
                                    sug_low, sug_high, len(market_rates),
                                    loc_adj, profile_adj, pp, 0, base_min, base_max)

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

def _algo_reasoning(req, customer, p_label, profile, customer_avg,
                    market_low, market_median, market_high,
                    sug_low, sug_high, sample_size,
                    loc_adj, profile_adj, pp, lost_count, base_min, base_max) -> str:
    name = customer.get("name", req.customer_name or "Customer")
    unit = "MT"

    parts: list[str] = []
    if req.category_id == "Custom":
        return f"Custom quotation for {name}. Floor price calculated from current rates without historical adjustments."

    if profile == "repeat_known_product":
        parts.append(f"{name} has bought {p_label} before — historical avg ₹{customer_avg:,.0f}/{unit}.")
    elif profile == "repeat_new_product":
        parts.append(f"{name} is a known customer but has not bought {p_label} before.")
    elif profile == "new_customer":
        parts.append(f"{name} is a new customer.")

    if base_min > 0:
        parts.append(f"Base margin applied: {base_min:.1f}% to {base_max:.1f}%.")
        if loc_adj != 0: parts.append(f"Region adds {loc_adj}%.")
        if profile_adj != 0: parts.append(f"Competitiveness tilt adds {profile_adj}%.")

    if pp != 0: parts.append(f"'{req.payment_terms}' adds {pp:.1f}%.")
    if sug_low and sug_high: parts.append(f"Recommended quote: ₹{int(sug_low):,} – ₹{int(sug_high):,}/{unit}.")
    return " ".join(parts)

def _ai_reasoning(req, customer, p_label, customer_avg, market_median, sug_low, sug_high) -> str:
    if req.category_id == "Custom":
        return "Custom Quote: Please review the floor price generated based on current raw material rates. Custom configurations lack historical data so no suggestions were made."
    is_repeat = bool(customer.get("is_repeat")) or int(customer.get("total_orders") or 0) > 0
    target = ((sug_low or 0) + (sug_high or 0)) / 2 if (sug_low and sug_high) else 0
    return AerialEngine.generate_reasoning(
        request_data={"product_type": p_label, "product_code": ""},
        math_context={"floor_price_mt": 0, "target_price_mt": target, "historical_avg_price": customer_avg or market_median},
        customer_stats={"name": customer.get("name", req.customer_name or ""), "is_repeat": is_repeat, "total_orders": int(customer.get("total_orders") or 0)}
    )
'''

with open('backend/app/pricing_engine.py', 'w', encoding='utf-8') as f:
    f.write(new_content + rest)
