"""
Quote Intelligence Engine.

Assembles all context data for a quote enquiry and generates
a mock AI response (to be replaced with Claude API later).
"""
from datetime import date, timedelta
import random
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import Product, Customer, QuoteHistory, FGInventory, Machine, RMPrice
from app.schemas import (
    ContextCard, MarketSignal, QuoteHistoryRow,
    PriceRangeOut, AIReasoning, QuoteResponse,
)

# Conversion cost estimates (₹/MT) — from master prompt Section 7
CONVERSION_COSTS = {
    "MS Wire": 3000,
    "HC Patented Wire": 4500,
    "GI Wire": 5500,
    "OFC Cable": 8000,  # per KME
}


def get_quote_suggestion(
    db: Session,
    customer_name: str,
    product_type: str,
    size_label: str,
    quantity: float,
    unit: str,
    payment_terms: str,
) -> QuoteResponse:
    """Main entry point — assembles all intelligence for a quote."""

    # ── 1. Customer classification ──────────────────────────────────────
    customer = db.query(Customer).filter(Customer.name == customer_name).first()
    is_repeat = customer.is_repeat if customer else False
    past_orders = customer.total_orders if customer else 0
    customer_type = "repeat" if is_repeat else "new"

    # ── 2. Last price to this customer for this product ─────────────────
    last_quote = (
        db.query(QuoteHistory)
        .filter(
            QuoteHistory.customer_name == customer_name,
            QuoteHistory.product_type == product_type,
            QuoteHistory.size_label == size_label,
        )
        .order_by(desc(QuoteHistory.quote_date))
        .first()
    )

    last_rate_str = f"₹{last_quote.unit_rate_inr:,.0f}/{last_quote.unit}" if last_quote else "No history"
    last_date_str = last_quote.quote_date.strftime("%d-%b-%Y") if last_quote else ""
    last_outcome = last_quote.outcome if last_quote else ""

    # ── 3. FG stock available ──────────────────────────────────────────
    fg_total = (
        db.query(func.sum(FGInventory.quantity_mt))
        .filter(
            FGInventory.product_type == product_type,
            FGInventory.size_label == size_label,
            FGInventory.inventory_type == "FG",
        )
        .scalar()
    ) or 0.0

    # If no exact match, try just product type
    if fg_total == 0:
        fg_total = (
            db.query(func.sum(FGInventory.quantity_mt))
            .filter(
                FGInventory.product_type == product_type,
                FGInventory.inventory_type == "FG",
            )
            .scalar()
        ) or 0.0

    can_dispatch_now = fg_total >= quantity
    fg_text = f"{fg_total:.1f} {unit}"
    fg_sub = "Ready to dispatch now" if can_dispatch_now else (
        f"Partial — {fg_total:.1f} available, {quantity - fg_total:.1f} needs production"
        if fg_total > 0
        else "Not in stock — production required"
    )

    # ── 4. Machine utilisation ─────────────────────────────────────────
    machine_type_map = {
        "MS Wire": "medium_drawing",
        "HC Patented Wire": "hc_drawing",
        "GI Wire": "galvanising",
        "OFC Cable": "ofc_line",
    }
    mt = machine_type_map.get(product_type, "medium_drawing")
    machines = db.query(Machine).filter(Machine.machine_type == mt).all()
    if not machines:
        machines = db.query(Machine).filter(Machine.product_types.contains(product_type)).all()

    avg_util = sum(m.current_utilisation_pct for m in machines) / len(machines) if machines else 0
    best_machine = min(machines, key=lambda m: m.current_utilisation_pct) if machines else None
    machine_unit = best_machine.unit_name if best_machine else "N/A"
    machine_text = f"{avg_util:.0f}%"
    machine_sub = f"{machine_unit} — {best_machine.machine_code if best_machine else 'N/A'}"

    # ── 5. RM cost ────────────────────────────────────────────────────
    rm_grade_map = {
        "MS Wire": "IS 7887 G-4",
        "HC Patented Wire": "HC72B",
        "GI Wire": "IS 7887 G-4",
        "OFC Cable": "OFC Raw",
    }
    rm_grade = rm_grade_map.get(product_type, "IS 7887 G-4")
    rm = (
        db.query(RMPrice)
        .filter(RMPrice.rm_grade == rm_grade)
        .order_by(desc(RMPrice.effective_date))
        .first()
    )
    rm_rate = rm.rate_per_mt_inr if rm else 52000
    rm_vendor = rm.vendor_name if rm else "Market estimate"
    rm_text = f"₹{rm_rate:,.0f}/MT"
    rm_sub = f"{rm_vendor} — {rm_grade}"

    # ── 6. Recent quotes (same product, all customers) ─────────────────
    recent_quotes_db = (
        db.query(QuoteHistory)
        .filter(
            QuoteHistory.product_type == product_type,
            QuoteHistory.size_label == size_label,
        )
        .order_by(desc(QuoteHistory.quote_date))
        .limit(5)
        .all()
    )

    recent_quotes = [
        QuoteHistoryRow(
            quote_date=q.quote_date,
            customer_name=q.customer_name,
            unit_rate_inr=q.unit_rate_inr,
            unit=q.unit,
            quantity=q.quantity,
            outcome=q.outcome,
        )
        for q in recent_quotes_db
    ]

    # ── 7. Market rate range ──────────────────────────────────────────
    thirty_days_ago = date.today() - timedelta(days=30)
    market_rates = (
        db.query(
            func.min(QuoteHistory.unit_rate_inr),
            func.max(QuoteHistory.unit_rate_inr),
            func.avg(QuoteHistory.unit_rate_inr),
        )
        .filter(
            QuoteHistory.product_type == product_type,
            QuoteHistory.size_label == size_label,
            QuoteHistory.quote_date >= thirty_days_ago,
        )
        .first()
    )

    market_low = market_rates[0] if market_rates[0] else rm_rate * 1.1
    market_high = market_rates[1] if market_rates[1] else rm_rate * 1.3
    market_avg = market_rates[2] if market_rates[2] else rm_rate * 1.2

    # ── 8. Dispatch ETA ───────────────────────────────────────────────
    if can_dispatch_now:
        eta_days = 2
        eta_text = "1–2 days"
        eta_sub = "FG in stock — ready for packing"
    elif fg_total > 0:
        mt_needed = quantity - fg_total
        daily_capacity = best_machine.capacity_mt_per_day if best_machine else 10
        prod_days = max(1, int(mt_needed / daily_capacity) + 1)
        eta_days = prod_days + 2
        eta_text = f"{eta_days} days"
        eta_sub = f"{fg_total:.1f} MT from stock + {prod_days}d production + 2d logistics"
    else:
        daily_capacity = best_machine.capacity_mt_per_day if best_machine else 10
        prod_days = max(1, int(quantity / daily_capacity) + 1)
        eta_days = prod_days + 3
        eta_text = f"{eta_days}–{eta_days + 2} days"
        eta_sub = f"Full production needed: {prod_days}d + 3d logistics buffer"

    # ── 9. Build context cards ────────────────────────────────────────
    context_cards = [
        ContextCard(
            label="Customer Type",
            value=f"{'Repeat' if is_repeat else 'New'} Customer",
            sub_text=f"{past_orders} past orders" if past_orders > 0 else "First-time enquiry",
            icon="user",
        ),
        ContextCard(
            label="Last Quoted",
            value=last_rate_str,
            sub_text=f"{last_date_str} — {last_outcome.upper()}" if last_date_str else "No prior quotes to this customer",
            icon="tag",
        ),
        ContextCard(
            label="FG Stock Available",
            value=fg_text,
            sub_text=fg_sub,
            icon="box",
        ),
        ContextCard(
            label="Machine Utilisation",
            value=machine_text,
            sub_text=machine_sub,
            icon="gauge",
        ),
        ContextCard(
            label="Estimated Dispatch",
            value=eta_text,
            sub_text=eta_sub,
            icon="truck",
        ),
        ContextCard(
            label="RM Cost",
            value=rm_text,
            sub_text=rm_sub,
            icon="dollar",
        ),
    ]

    # ── 10. Market signals ────────────────────────────────────────────
    signals = _build_market_signals(
        is_repeat, past_orders, last_quote, fg_total, quantity,
        avg_util, payment_terms, market_low, market_high, eta_days,
    )

    # ── 11. Price range + AI reasoning ────────────────────────────────
    conversion_cost = CONVERSION_COSTS.get(product_type, 3000)
    floor_price = rm_rate + conversion_cost  # cost + minimum margin

    # Suggested range: between floor+10% and market ceiling
    suggested_low = max(floor_price * 1.10, market_low * 0.98) if market_low else floor_price * 1.10
    suggested_high = min(floor_price * 1.25, market_high * 1.02) if market_high else floor_price * 1.25

    # Adjust for payment terms
    credit_premium = {"Advance": -0.01, "30 Days": 0.0, "45 Days": 0.01, "60 Days": 0.02}
    adjustment = credit_premium.get(payment_terms, 0)
    suggested_low *= (1 + adjustment)
    suggested_high *= (1 + adjustment)

    price_range = PriceRangeOut(
        floor_price=round(floor_price, 0),
        suggested_low=round(suggested_low, 0),
        suggested_high=round(suggested_high, 0),
        market_ceiling=round(market_high, 0),
        unit=unit,
    )

    # Mock AI reasoning
    ai_text = _generate_mock_reasoning(
        customer_name, product_type, size_label, quantity, unit,
        payment_terms, is_repeat, past_orders, last_quote,
        fg_total, avg_util, rm_rate, conversion_cost,
        suggested_low, suggested_high, market_low, market_high,
        eta_days, can_dispatch_now,
    )

    return QuoteResponse(
        context_cards=context_cards,
        market_signals=signals,
        price_range=price_range,
        ai_reasoning=AIReasoning(text=ai_text, is_stubbed=True),
        recent_quotes=recent_quotes,
        customer_type=customer_type,
        past_order_count=past_orders,
    )


def _build_market_signals(
    is_repeat, past_orders, last_quote, fg_total, quantity,
    avg_util, payment_terms, market_low, market_high, eta_days,
) -> list[MarketSignal]:
    """Generate colour-coded market signal indicators."""
    signals = []

    # Green signals (favourable)
    if fg_total >= quantity:
        signals.append(MarketSignal(color="green", text=f"Full FG stock available — {fg_total:.1f} MT ready for immediate dispatch"))
    if is_repeat and past_orders >= 3:
        signals.append(MarketSignal(color="green", text=f"Loyal repeat customer with {past_orders} past orders — strong relationship"))
    if last_quote and last_quote.outcome == "won":
        signals.append(MarketSignal(color="green", text=f"Won the last quote to this customer at ₹{last_quote.unit_rate_inr:,.0f}/{last_quote.unit}"))
    if payment_terms == "Advance":
        signals.append(MarketSignal(color="green", text="Advance payment — zero credit risk, consider offering a competitive rate"))

    # Amber signals (watch)
    if 40 <= avg_util <= 70:
        signals.append(MarketSignal(color="amber", text=f"Machine utilisation at {avg_util:.0f}% — moderate capacity load"))
    if fg_total > 0 and fg_total < quantity:
        signals.append(MarketSignal(color="amber", text=f"Partial stock available ({fg_total:.1f} MT) — balance requires production scheduling"))

    # Red signals (risk)
    if fg_total == 0:
        signals.append(MarketSignal(color="red", text="Zero FG stock — full production needed, longer dispatch timeline"))
    if last_quote and last_quote.outcome == "lost":
        signals.append(MarketSignal(color="red", text=f"Lost the last quote to this customer — may need to be more competitive"))
    if avg_util > 85:
        signals.append(MarketSignal(color="red", text=f"Machine utilisation at {avg_util:.0f}% — production line is heavily loaded"))
    if eta_days > 10:
        signals.append(MarketSignal(color="red", text=f"Extended delivery timeline ({eta_days}+ days) — may affect customer decision"))

    # Blue signals (informational)
    credit_days_map = {"Advance": 0, "30 Days": 30, "45 Days": 45, "60 Days": 60}
    credit_days = credit_days_map.get(payment_terms, 30)
    signals.append(MarketSignal(color="blue", text=f"Payment terms: {payment_terms} ({credit_days} days credit)"))
    if market_low and market_high:
        signals.append(MarketSignal(color="blue", text=f"Market rate range (last 30 days): ₹{market_low:,.0f} – ₹{market_high:,.0f}"))

    # Ensure we have at least 3 signals
    if not is_repeat:
        signals.append(MarketSignal(color="blue", text="New customer — no pricing history available, use market benchmarks"))

    return signals


def _generate_mock_reasoning(
    customer_name, product_type, size_label, quantity, unit,
    payment_terms, is_repeat, past_orders, last_quote,
    fg_total, avg_util, rm_rate, conversion_cost,
    suggested_low, suggested_high, market_low, market_high,
    eta_days, can_dispatch_now,
) -> str:
    """
    Generate a realistic, context-aware mock AI response.
    This will be replaced by Claude API when API key is available.
    """
    total_cost = rm_rate + conversion_cost
    margin_low_pct = ((suggested_low - total_cost) / total_cost * 100)
    margin_high_pct = ((suggested_high - total_cost) / total_cost * 100)

    parts = []

    # Opening — customer context
    if is_repeat and past_orders >= 5:
        parts.append(
            f"{customer_name} is a well-established repeat customer with {past_orders} past orders. "
            f"Maintaining this relationship should be prioritised, but not at the expense of margins."
        )
    elif is_repeat:
        parts.append(
            f"{customer_name} is a returning customer with {past_orders} previous order(s). "
            f"There's an opportunity to strengthen this relationship with competitive pricing."
        )
    else:
        parts.append(
            f"{customer_name} is a new customer with no prior order history. "
            f"Consider a slightly competitive rate to win the first order, while maintaining healthy margins."
        )

    # Pricing rationale
    if last_quote and last_quote.outcome == "won":
        parts.append(
            f"The last quote to this customer was at ₹{last_quote.unit_rate_inr:,.0f}/{unit} "
            f"and was won — suggesting the customer is price-sensitive around this level. "
            f"Adjusting for current RM costs (₹{rm_rate:,.0f}/MT) and a conversion cost of ₹{conversion_cost:,.0f}/MT, "
            f"the floor price is ₹{total_cost:,.0f}/{unit}."
        )
    elif last_quote and last_quote.outcome == "lost":
        parts.append(
            f"The last quote at ₹{last_quote.unit_rate_inr:,.0f}/{unit} was lost — the customer likely found a lower rate. "
            f"Consider quoting closer to ₹{suggested_low:,.0f}/{unit} to improve win probability, "
            f"which still preserves a {margin_low_pct:.1f}% margin above cost (₹{total_cost:,.0f}/{unit})."
        )
    else:
        parts.append(
            f"With current RM cost at ₹{rm_rate:,.0f}/MT and conversion cost of ₹{conversion_cost:,.0f}/MT, "
            f"the cost base is ₹{total_cost:,.0f}/{unit}. "
            f"The suggested range of ₹{suggested_low:,.0f}–₹{suggested_high:,.0f} provides a "
            f"{margin_low_pct:.1f}%–{margin_high_pct:.1f}% margin."
        )

    # Stock & dispatch
    if can_dispatch_now:
        parts.append(
            f"With {fg_total:.1f} {unit} in finished goods stock, the full quantity of {quantity:.1f} {unit} "
            f"can be dispatched within 1–2 days — this is a strong selling point that can justify pricing at the higher end."
        )
    elif fg_total > 0:
        parts.append(
            f"Partial stock of {fg_total:.1f} {unit} is available for immediate dispatch, "
            f"with the remaining {quantity - fg_total:.1f} {unit} requiring {eta_days - 2} days of production. "
            f"Quote in the mid-range to balance competitive pricing with production scheduling constraints."
        )
    else:
        parts.append(
            f"No finished goods stock is currently available — the full {quantity:.1f} {unit} requires "
            f"production scheduling with an estimated {eta_days}-day delivery timeline. "
            f"Machine utilisation is at {avg_util:.0f}%, so capacity is {'tight' if avg_util > 75 else 'manageable'}."
        )

    # Payment terms adjustment
    if payment_terms == "Advance":
        parts.append("Advance payment eliminates credit risk — a slight discount of 1% from the standard rate is reasonable.")
    elif payment_terms in ("45 Days", "60 Days"):
        parts.append(f"{payment_terms} credit terms carry working capital cost — factor in a 1–2% premium over standard rates.")

    return " ".join(parts)
