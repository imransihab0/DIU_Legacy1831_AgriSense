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


def market_price_intelligence(crop: str, max_store_months: int = MAX_STORE_MONTHS) -> dict:
    """Current + modeled historical prices and a sell/store/wait recommendation."""
    pk = _resolve(crop)
    if not pk:
        return {"error": f"No price data for '{crop}'. Valid: {list(_SEAS)}"}
    p = _SEAS[pk]
    today = date.today()
    # month-aware modeled price so "now" is consistent with the seasonal curve used
    # for the store/wait projection; the static catalog price is kept as a reference.
    current_price = _price(p, today.month)
    catalog_price = _MARKET.get(pk, {}).get("farm_gate")

    # modeled 12-month history (trailing)
    history = []
    for i in range(11, -1, -1):
        y, m = _add_months(today.year, today.month, -i)
        history.append({"month": f"{y}-{m:02d} ({_MONTHS[m]})", "price_bdt_per_kg": _price(p, m)})
    cycle = [_price(p, m) for m in range(1, 13)]
    lo, hi, med = min(cycle), max(cycle), round(sorted(cycle)[6], 2)

    # where are we in the cycle now?
    cur_model = _price(p, today.month)
    if cur_model <= lo + (hi - lo) / 3:
        position = "near the seasonal LOW (harvest glut) — a poor time to sell if you can store"
    elif cur_model >= hi - (hi - lo) / 3:
        position = "near the seasonal PEAK — a good time to sell"
    else:
        position = "mid-cycle"

    # sell / store / wait
    if not p["storable"]:
        rec = {"action": "sell_now",
               "reason": f"{_MARKET.get(pk,{}).get('crop',pk)} is highly perishable (~{p['spoilage_pct_per_month']}%/month loss) — storing is not viable. Sell at harvest."}
        best = {"months": 0, "projected_price_bdt_per_kg": current_price, "net_after_costs_bdt_per_kg": current_price}
    else:
        best = {"months": 0, "projected_price_bdt_per_kg": current_price, "net_after_costs_bdt_per_kg": current_price}
        for n in range(1, max_store_months + 1):
            _, fm = _add_months(today.year, today.month, n)
            proj = _price(p, fm)
            net = round(proj * (1 - p["spoilage_pct_per_month"] / 100 * n) - p["storage_cost_bdt_per_kg_month"] * n, 2)
            if net > best["net_after_costs_bdt_per_kg"]:
                best = {"months": n, "projected_price_bdt_per_kg": proj, "net_after_costs_bdt_per_kg": net}
        gain = round(best["net_after_costs_bdt_per_kg"] - current_price, 2)
        gain_pct = round(gain / current_price * 100, 1) if current_price else 0
        if best["months"] == 0 or gain_pct < 5:
            rec = {"action": "sell_now",
                   "reason": f"Storing doesn't beat selling now: best net after storage/spoilage is ৳{best['net_after_costs_bdt_per_kg']}/kg vs ৳{current_price}/kg current (only {gain_pct}% gain). Sell now and free up cash."}
        else:
            _, tm = _add_months(today.year, today.month, best["months"])
            rec = {"action": "store" if best["months"] >= 2 else "wait",
                   "reason": f"Prices rise toward {_MONTHS[tm]}: storing ~{best['months']} month(s) nets ~৳{best['net_after_costs_bdt_per_kg']}/kg after storage+spoilage vs ৳{current_price}/kg now (+{gain_pct}%).",
                   "target_month": _MONTHS[tm], "expected_net_bdt_per_kg": best["net_after_costs_bdt_per_kg"]}

    return {
        "crop": _MARKET.get(pk, {}).get("crop", pk),
        "current_price_bdt_per_kg": current_price,
        "current_price_source": "modeled seasonal price for the current month (seeded; swap to DAM feed when available)",
        "catalog_reference_bdt_per_kg": catalog_price,
        "seasonal_position": position,
        "modeled_12_month": {"low": lo, "high": hi, "median": med,
                             "low_month": _MONTHS[cycle.index(lo) + 1], "high_month": _MONTHS[cycle.index(hi) + 1]},
        "history_monthly": history,
        "storage": {"storable": p["storable"], "cost_bdt_per_kg_month": p["storage_cost_bdt_per_kg_month"],
                    "spoilage_pct_per_month": p["spoilage_pct_per_month"]},
        "recommendation": rec,
        "disclaimer": "SEEDED/MODELED seasonal prices (labeled) — not a live feed. Confirm at your local market/DAM before selling.",
    }
