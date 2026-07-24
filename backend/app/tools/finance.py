"""Deterministic financial engine (Tier 0 #5).

All arithmetic happens here in Python — never in the LLM — so the math is
inspectable, internally consistent, and changes correctly when inputs change.
Also powers Tier 1 scenario simulation via the *_factor overrides.
"""
import json
from ..config import DATA_DIR

_CROPS = json.loads((DATA_DIR / "crops.json").read_text())["crops"]
_PRICES = json.loads((DATA_DIR / "market_prices.json").read_text())["prices"]


def list_crops() -> dict:
    return {
        k: {
            "display": v["display"], "season": v["season"],
            "sowing_window": v["sowing_window"], "duration_days": v["duration_days"],
            "water_need": v["water_need"], "risk_level": v["risk_level"],
            "suitable_soils": v["suitable_soils"],
        }
        for k, v in _CROPS.items()
    }


def compute_financials(
    crop: str,
    area_acres: float,
    budget_bdt: float | None = None,
    price_per_kg: float | None = None,
    yield_factor: float = 1.0,
    cost_factor: float = 1.0,
    price_factor: float = 1.0,
) -> dict:
    key = crop.lower().strip().replace(" ", "_")
    if key not in _CROPS:
        return {"error": f"Unknown crop '{crop}'. Valid keys: {list(_CROPS)}"}
    c = _CROPS[key]
    area = float(area_acres)

    base_price = price_per_kg if price_per_kg else _PRICES[c["price_key"]]["farm_gate"]
    price = round(base_price * price_factor, 2)
    yield_kg = round(c["yield_kg_per_acre"] * yield_factor * area)

    items = {
        name: round(amount * cost_factor * area)
        for name, amount in c["costs_bdt_per_acre"].items()
    }
    total_cost = sum(items.values())
    revenue = round(yield_kg * price)
    net_profit = revenue - total_cost
    roi_pct = round(net_profit / total_cost * 100, 1) if total_cost else None
    breakeven_price = round(total_cost / yield_kg, 2) if yield_kg else None
    breakeven_yield_kg = round(total_cost / price) if price else None

    result = {
        "crop": c["display"],
        "area_acres": area,
        "assumptions": {
            "yield_kg_per_acre_baseline": c["yield_kg_per_acre"],
            "price_per_kg_bdt": price,
            "price_source": "farmer-provided" if price_per_kg else "seeded market catalog (mock, labeled)",
            "yield_factor": yield_factor, "cost_factor": cost_factor, "price_factor": price_factor,
        },
        "cost_breakdown_bdt": items,
        "total_cost_bdt": total_cost,
        "expected_yield_kg": yield_kg,
        "expected_revenue_bdt": revenue,
        "net_profit_bdt": net_profit,
        "roi_pct": roi_pct,
        "breakeven_price_bdt_per_kg": breakeven_price,
        "breakeven_yield_kg": breakeven_yield_kg,
    }
    if budget_bdt is not None:
        result["budget_bdt"] = budget_bdt
        result["within_budget"] = total_cost <= float(budget_bdt)
        result["budget_gap_bdt"] = round(float(budget_bdt) - total_cost)
    return result
