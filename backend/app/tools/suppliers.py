"""Supplier / marketplace comparison (Tier 2, seeded catalog).

Ranks input dealers for a given item by price, delivery time, distance and rating.
The brief explicitly accepts a seeded/mock catalog (suppliers.json).
"""
import json
from ..config import DATA_DIR

_DATA = json.loads((DATA_DIR / "suppliers.json").read_text())
_SUPPLIERS = _DATA["suppliers"]


def _norm(item: str) -> str:
    return item.lower().strip().replace(" ", "_")


def compare_suppliers(item: str, quantity: float | None = None, sort_by: str = "price") -> dict:
    """Rank suppliers that stock `item`. sort_by: price | delivery | distance | rating."""
    key = _norm(item)
    rows = []
    for s in _SUPPLIERS:
        if key not in s["prices"]:
            continue
        unit_price = s["prices"][key]
        rows.append({
            "supplier": s["name"], "location": s["location"],
            "unit_price_bdt": unit_price,
            "line_total_bdt": round(unit_price * quantity) if quantity else None,
            "delivery_days": s["delivery_days"], "distance_km": s["distance_km"], "rating": s["rating"],
        })
    if not rows:
        stocked = sorted({k for s in _SUPPLIERS for k in s["prices"]})
        return {"error": f"No supplier stocks '{item}'. Stocked items: {stocked}"}

    keyfns = {
        "price": lambda r: (r["unit_price_bdt"], r["delivery_days"]),
        "delivery": lambda r: (r["delivery_days"], r["unit_price_bdt"]),
        "distance": lambda r: (r["distance_km"], r["unit_price_bdt"]),
        "rating": lambda r: (-r["rating"], r["unit_price_bdt"]),
    }
    sort_by = sort_by if sort_by in keyfns else "price"
    rows.sort(key=keyfns[sort_by])

    cheapest = min(rows, key=lambda r: r["unit_price_bdt"])
    fastest = min(rows, key=lambda r: r["delivery_days"])
    best_rated = max(rows, key=lambda r: r["rating"])
    return {
        "item": item,
        "quantity": quantity,
        "sorted_by": sort_by,
        "suppliers": rows,
        "best_price": {"supplier": cheapest["supplier"], "unit_price_bdt": cheapest["unit_price_bdt"]},
        "fastest": {"supplier": fastest["supplier"], "delivery_days": fastest["delivery_days"]},
        "best_rated": {"supplier": best_rated["supplier"], "rating": best_rated["rating"]},
        "disclaimer": "SEEDED/MOCK supplier catalog (labeled per rules) — not a live marketplace.",
    }
