"""Market price intelligence — historical trend + sell/store/wait advice (Tier 2).

Models a monthly price series from seeded per-crop seasonality (price_seasonality.json)
and gives a deterministic sell-now / store / wait recommendation that accounts for the
seasonal trend, storage cost and spoilage. Current price comes from the seeded market
catalog (swap to a real DAM feed when available). All labeled seeded per the rules.
"""
import json
import math
from datetime import date
from ..config import DATA_DIR

_SEAS = json.loads((DATA_DIR / "price_seasonality.json").read_text())["crops"]
_MARKET = json.loads((DATA_DIR / "market_prices.json").read_text())["prices"]
_CROPS = json.loads((DATA_DIR / "crops.json").read_text())["crops"]

MAX_STORE_MONTHS = 6
_MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _resolve(crop: str) -> str | None:
    key = crop.lower().strip().replace(" ", "_")
    if key in _SEAS:
        return key
    if key in _CROPS:  # e.g. boro_rice -> rice_paddy
        pk = _CROPS[key].get("price_key")
        if pk in _SEAS:
            return pk
    return None


def _mult(params: dict, month: int) -> float:
    """Seasonal multiplier: lowest (1-amp) at the harvest-trough month, highest opposite."""
    phase = 2 * math.pi * (month - params["trough_month"]) / 12
    return 1 - params["amplitude"] * math.cos(phase)


def _price(params: dict, month: int) -> float:
    return round(params["base_price"] * _mult(params, month), 2)


def _add_months(y: int, m: int, delta: int) -> tuple[int, int]:
    idx = (y * 12 + (m - 1)) + delta
    return idx // 12, idx % 12 + 1


def market_price_intelligence(
    crop: str,
    max_store_months: int = MAX_STORE_MONTHS,
    current_price: float | None = None,
    prev_month_price: float | None = None,
    prev_year_price: float | None = None,
) -> dict:
    """Sell / store / wait recommendation.

    If REAL DAM prices are passed (current_price, and optionally prev_month_price /
    prev_year_price from the DAM division report), the analysis is anchored to them and
    the real month-over-month trend drives the call. Otherwise it falls back to the
    modeled seasonal curve. Storage cost + spoilage are always factored deterministically.
    """
    pk = _resolve(crop)
    if not pk:
        return {"error": f"No price data for '{crop}'. Valid: {list(_SEAS)}"}
    p = _SEAS[pk]
    today = date.today()
    modeled_now = _price(p, today.month)

    real = current_price is not None
    cur = round(float(current_price), 2) if real else modeled_now
    scale = (cur / modeled_now) if (real and modeled_now) else 1.0  # anchor modeled shape to real price

    def proj(month):
        return round(_price(p, month) * scale, 2)

    # real trend from the DAM report (if provided)
    trend = {}
    if real and prev_month_price:
        trend["month_over_month_pct"] = round((cur - prev_month_price) / prev_month_price * 100, 1)
    if real and prev_year_price:
        trend["year_over_year_pct"] = round((cur - prev_year_price) / prev_year_price * 100, 1)
    mom = trend.get("month_over_month_pct")

    history = [{"month": f"{y}-{m:02d} ({_MONTHS[m]})", "price_bdt_per_kg": proj(m)}
               for y, m in (_add_months(today.year, today.month, -i) for i in range(11, -1, -1))]
    cycle = [proj(m) for m in range(1, 13)]
    lo, hi, med = min(cycle), max(cycle), round(sorted(cycle)[6], 2)
    lo0, hi0 = min(_price(p, m) for m in range(1, 13)), max(_price(p, m) for m in range(1, 13))
    if modeled_now <= lo0 + (hi0 - lo0) / 3:
        position = "near the seasonal LOW (harvest glut) — a poor time to sell if you can store"
    elif modeled_now >= hi0 - (hi0 - lo0) / 3:
        position = "near the seasonal PEAK — a good time to sell"
    else:
        position = "mid-cycle"

    # ---- decision ----
    if not p["storable"]:
        rec = {"action": "sell_now",
               "reason": f"{_MARKET.get(pk,{}).get('crop',pk)} is highly perishable (~{p['spoilage_pct_per_month']}%/month loss) — storing is not viable. Sell at harvest."}
    elif mom is not None and mom <= -3:
        rec = {"action": "sell_now",
               "reason": f"Per the DAM report the market is FALLING ({mom}% vs last month) — sell now before it drops further."}
    else:
        best = {"months": 0, "projected_price_bdt_per_kg": cur, "net_after_costs_bdt_per_kg": cur}
        for n in range(1, max_store_months + 1):
            _, fm = _add_months(today.year, today.month, n)
            pr = proj(fm)
            net = round(pr * (1 - p["spoilage_pct_per_month"] / 100 * n) - p["storage_cost_bdt_per_kg_month"] * n, 2)
            if net > best["net_after_costs_bdt_per_kg"]:
                best = {"months": n, "projected_price_bdt_per_kg": pr, "net_after_costs_bdt_per_kg": net}
        gain_pct = round((best["net_after_costs_bdt_per_kg"] - cur) / cur * 100, 1) if cur else 0
        if best["months"] == 0 or gain_pct < 5:
            rec = {"action": "sell_now",
                   "reason": f"Storing doesn't beat selling now: best net after storage/spoilage is ৳{best['net_after_costs_bdt_per_kg']}/kg vs ৳{cur}/kg now (only {gain_pct}% gain). Sell now and free up cash."}
        else:
            _, tm = _add_months(today.year, today.month, best["months"])
            reason = f"Prices typically rise toward {_MONTHS[tm]}: storing ~{best['months']} month(s) nets ~৳{best['net_after_costs_bdt_per_kg']}/kg after storage+spoilage vs ৳{cur}/kg now (+{gain_pct}%)."
            if mom is not None and mom > 2:
                reason += f" The DAM trend is also up {mom}% vs last month."
            rec = {"action": "store" if best["months"] >= 2 else "wait",
                   "reason": reason, "target_month": _MONTHS[tm],
                   "expected_net_bdt_per_kg": best["net_after_costs_bdt_per_kg"]}

    return {
        "crop": _MARKET.get(pk, {}).get("crop", pk),
        "current_price_bdt_per_kg": cur,
        "current_price_source": "REAL DAM report price" if real else "modeled seasonal (seeded)",
        "real_trend": trend or None,
        "catalog_reference_bdt_per_kg": _MARKET.get(pk, {}).get("farm_gate"),
        "seasonal_position": position,
        "modeled_12_month": {"low": lo, "high": hi, "median": med,
                             "low_month": _MONTHS[cycle.index(lo) + 1], "high_month": _MONTHS[cycle.index(hi) + 1]},
        "history_monthly": history,
        "storage": {"storable": p["storable"], "cost_bdt_per_kg_month": p["storage_cost_bdt_per_kg_month"],
                    "spoilage_pct_per_month": p["spoilage_pct_per_month"]},
        "recommendation": rec,
        "disclaimer": ("Combines the REAL DAM current price + month/year trend with deterministic storage/spoilage economics."
                       if real else "SEEDED/MODELED seasonal prices (labeled). For a real figure, pass the DAM report price (search_knowledge_base)."),
    }
